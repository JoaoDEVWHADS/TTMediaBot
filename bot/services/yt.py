from __future__ import annotations
import http.cookiejar
import logging
import time
import os
import asyncio
import shutil
import tempfile
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from bot import Bot

from yt_dlp import YoutubeDL
from yt_dlp.downloader import get_suitable_downloader
from yt_dlp.utils import DownloadError
from py_yt.search import VideosSearch


from bot.config.models import YtModel

from bot.player.enums import TrackType
from bot.player.track import Track
from bot.services import Service as _Service
from bot import errors


class YtService(_Service):
    def __init__(self, bot: Bot, config: YtModel):
        self.bot = bot
        self.config = config
        self.name = "yt"
        self.hostnames = []
        self.is_enabled = self.config.enabled
        self.error_message = ""
        self.warning_message = ""
        self.help = ""
        self.hidden = False
        self._cookie_lock = threading.Lock()
        self._max_retries = 2

    def initialize(self):
        # Validate cookie file at startup
        if self.config.cookiefile_path:
            if os.path.isfile(self.config.cookiefile_path):
                logging.info(f"YT Service: Cookie file found at {self.config.cookiefile_path}")
            else:
                logging.warning(
                    f"YT Service: Cookie file NOT FOUND at '{self.config.cookiefile_path}'. "
                    "YouTube may block requests. Please provide a valid cookies.txt file."
                )
        else:
            logging.warning(
                "YT Service: No cookie file configured (cookiefile_path is empty). "
                "YouTube may block requests requiring authentication."
            )

        self._ydl_config = {
            "skip_download": True,
            "format": "ba[ext=m4a]/ba[ext=webm]/ba/bestaudio/best",
            "format_sort": ["codec:opus", "codec:m4a", "codec:mp3", "res:144"],
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "socket_timeout": 10,
            "logger": logging.getLogger("root"),
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "check_formats": False,
            "noplaylist": True,
            "js_runtimes": {"node": {}},
            "allowed_extractors": ["youtube", "youtube:playlist", "youtube:search", "youtube:tab"],
            "cachedir": False,
            "lazy_playlist": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["tv_downgraded", "web"],
                    "player_skip": ["android_vr", "android", "ios", "tv_simply"],
                }
            },
        }

        # Persistent event loop for faster async operations
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        # Pre-warming: establishing connections early
        threading.Thread(target=self._pre_warm, daemon=True).start()

        # Connection Keep-Alive to prevent TCP/SSL handshake lag
        threading.Thread(target=self._connection_keeper, daemon=True).start()

    def _pre_warm(self):
        # Wait a few seconds for Docker network interface to fully settle
        time.sleep(5)
        for attempt in range(1, 4):
            try:
                logging.info(f"YT Service pre-warming (attempt {attempt}/3)...")
                # Establish initial connection to YouTube
                self.search("music")
                logging.info("YT Service pre-warming finished successfully.")
                return
            except Exception as e:
                if attempt < 3:
                    logging.warning(f"YT Pre-warming attempt {attempt} failed: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    logging.error(f"YT Pre-warming failed after 3 attempts: {e}")

    @contextmanager
    def _temp_cookie_file(self) -> Generator[Optional[str], None, None]:
        if not self.config.cookiefile_path or not os.path.isfile(self.config.cookiefile_path):
            yield None
            return

        import uuid
        temp_cookie_path = os.path.join(
            tempfile.gettempdir(), 
            f"yt_cookies_{os.getpid()}_{uuid.uuid4().hex}.txt"
        )
        
        try:
            with self._cookie_lock:
                shutil.copy2(self.config.cookiefile_path, temp_cookie_path)
            yield temp_cookie_path
        finally:
            if os.path.isfile(temp_cookie_path):
                try:
                    os.remove(temp_cookie_path)
                except Exception as e:
                    logging.debug(f"Failed to remove temp cookie file {temp_cookie_path}: {e}")
            
    def download(self, track: Track, file_path: str, video: bool = False) -> None:
        start_time = time.perf_counter()
        info = track.extra_info
        if not info:
            super().download(track, file_path, video=video)
            duration = (time.perf_counter() - start_time) * 1000
            logging.info(f"YT Download finished in {duration:.2f}ms for {track.name}")
            return
        
        # Instantiate per request for thread safety
        config = self._ydl_config.copy()
        config["skip_download"] = False
        
        if not video:
            config["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        else:
            config["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            config["merge_output_format"] = "mp4"

        config["outtmpl"] = file_path.rsplit(".", 1)[0] + ".%(ext)s"

        url = track.url
        if track.extra_info:
            if "webpage_url" in track.extra_info:
                url = track.extra_info["webpage_url"]
            elif "id" in track.extra_info:
                url = f"https://www.youtube.com/watch?v={track.extra_info['id']}"

        with self._temp_cookie_file() as cookie_file:
            if cookie_file:
                config["cookiefile"] = cookie_file
            
            with YoutubeDL(config) as ydl:
                ydl.download([url])

        duration = (time.perf_counter() - start_time) * 1000
        logging.info(f"YT Download finished in {duration:.2f}ms for {track.name}")

    def get(
        self,
        url: str,
        extra_info: Optional[Dict[str, Any]] = None,
        process: bool = False,
    ) -> List[Track]:
        start_time = time.perf_counter()
        if not (url or extra_info):
            raise errors.InvalidArgumentError()
        
        last_error = None
        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                wait_time = 2 ** attempt
                logging.warning(f"YT Get: Retry {attempt}/{self._max_retries} for '{url}' after {wait_time}s delay")
                time.sleep(wait_time)

            try:
                return self._get_inner(url, extra_info, process, start_time)
            except errors.ServiceError as e:
                last_error = e
                error_msg = str(e)
                is_auth_error = "Sign in to confirm" in error_msg or "cookies" in error_msg.lower()
                if not is_auth_error or attempt >= self._max_retries:
                    raise
                logging.warning(f"YT Get: Auth-related error, will retry: {error_msg[:100]}")
        
        raise last_error or errors.ServiceError("Max retries exceeded")

    def _get_inner(
        self,
        url: str,
        extra_info: Optional[Dict[str, Any]],
        process: bool,
        start_time: float,
    ) -> List[Track]:
        config = self._ydl_config.copy()
        with self._temp_cookie_file() as cookie_file:
            if cookie_file:
                config["cookiefile"] = cookie_file
            elif self.config.cookiefile_path:
                logging.warning(
                    f"YT Get: Cookie file '{self.config.cookiefile_path}' not found. "
                    "Proceeding without cookies — YouTube may block this request."
                )
            
            ydl_start = time.perf_counter()
            with YoutubeDL(config) as ydl:
                ydl_duration = (time.perf_counter() - ydl_start) * 1000
                logging.info(f"YT Get: YoutubeDL initialized in {ydl_duration:.2f}ms")
                if extra_info:
                     info = extra_info
                     v_id = info.get("videoId") or info.get("contentId") or info.get("id")
                     if "url" not in info and v_id:
                         url = f"https://www.youtube.com/watch?v={v_id}"
                         try:
                             info = ydl.extract_info(url, process=False)
                         except DownloadError as e:
                             logging.error(f"YT Get: yt-dlp DownloadError for '{url}': {e}")
                             raise errors.ServiceError(str(e))
                else:
                    try:
                        info = ydl.extract_info(url, process=False)
                    except DownloadError as e:
                        error_msg = str(e)
                        if "Sign in to confirm" in error_msg or "cookies" in error_msg.lower():
                            logging.error(
                                f"YT Get: YouTube requires authentication for '{url}'. "
                                "Please provide a valid cookies.txt file. "
                                "See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
                            )
                        else:
                            logging.error(f"YT Get: yt-dlp DownloadError for '{url}': {error_msg}")
                            if "Signature solving failed" in error_msg or "JavaScript runtime" in error_msg:
                                logging.error("YT Get: Possible missing JavaScript runtime or challenge solver. Check if Node.js is correctly installed in the environment.")
                        raise errors.ServiceError(str(e))
                
                if info is None:
                    raise errors.ServiceError("Failed to extract video info")

                info_type = None
                if "_type" in info:
                    info_type = info["_type"]
                if info_type == "url" and not info.get("ie_key"):
                    return self.get(info["url"], process=False)
                elif info_type == "playlist":
                    tracks: List[Track] = []
                    playlist_title = info.get("title") or info.get("playlist_title")
                    playlist_uploader = info.get("uploader") or info.get("playlist_uploader")
                    
                    for entry in info["entries"]:
                        try:
                            # Inject playlist metadata into the entry so tracks carry it
                            if playlist_title:
                                entry["playlist_title"] = playlist_title
                            if playlist_uploader:
                                entry["playlist_uploader"] = playlist_uploader
                            
                            data = self.get("", extra_info=entry, process=False)
                            tracks += data
                        except errors.ServiceError:
                            logging.warning(f"YT Get: Skipping playlist entry due to error")
                            continue
                    duration = (time.perf_counter() - start_time) * 1000
                    logging.info(f"YT Get (Playlist) finished in {duration:.2f}ms for {url}")
                    return tracks
                if not process:
                    # Fetch related videos for queueing if it's a single video!
                    video_id = info.get("id") or info.get("videoId")
                    if not video_id and url:
                         if "v=" in url:
                              video_id = url.split("v=")[1].split("&")[0]
                         elif "youtu.be" in url:
                              video_id = url.split("/")[-1]
                    
                    if video_id:
                         try:
                              # First, add the original video track
                              original_title = info.get("title", self.bot.translator.translate("Unknown Title"))
                              if "uploader" in info:
                                   original_title += " - {}".format(info["uploader"])
                              
                              original_track = Track(
                                   service=self.name,
                                   url=f"https://www.youtube.com/watch?v={video_id}",
                                   name=original_title,
                                   type=TrackType.Dynamic,
                                   extra_info=info
                              )
                              
                              # Then fetch recommendations (limit to 20 matching YTM behavior)
                              recs = self._get_recommendations(video_id, limit=20)
                              duration = (time.perf_counter() - start_time) * 1000
                              logging.info(f"YT Get (Watch Playlist) finished in {duration:.2f}ms for video_id {video_id}")
                              return [original_track] + recs
                         except Exception as e:
                              logging.error(f"YT Watch Playlist failed: {e}")
                    
                    duration = (time.perf_counter() - start_time) * 1000
                    logging.info(f"YT Get (No Process) finished in {duration:.2f}ms for {url}")
                    return [
                        Track(service=self.name, extra_info=info, type=TrackType.Dynamic)
                    ]
                try:
                    stream = ydl.process_ie_result(info)
                except DownloadError as e:
                    logging.error(f"YT Get: Failed to process stream for '{url}': {e}")
                    raise errors.ServiceError(str(e))
                except Exception:
                    raise errors.ServiceError()
                
                if "url" in stream:
                    url = stream["url"]
                else:
                    raise errors.ServiceError("No stream URL found in processed result")
                title = stream["title"]
                if "uploader" in stream:
                    title += " - {}".format(stream["uploader"])
                format = "mp3"
                if "is_live" in stream and stream["is_live"]:
                    track_type = TrackType.Live
                else:
                    track_type = TrackType.Default
                
                # TRIGGER BACKGROUND AUTOPLAY FETCH (matching YTM behavior)
                current_video_id = None
                if extra_info:
                     current_video_id = extra_info.get("id") or extra_info.get("videoId")
                if not current_video_id and "id" in stream:
                     current_video_id = stream["id"]
                
                if current_video_id:
                     should_fetch = False
                     try:
                           if self.bot.player.track_list:
                                last_track = self.bot.player.track_list[-1]
                                last_video_id = None
                                if last_track.extra_info:
                                     last_video_id = last_track.extra_info.get('id') or last_track.extra_info.get('videoId')
                                
                                if not last_video_id and hasattr(last_track, '_url') and last_track._url:
                                     l_url = last_track._url
                                     if "v=" in l_url:
                                          last_video_id = l_url.split("v=")[1].split("&")[0]
                                     elif "youtu.be" in l_url:
                                          last_video_id = l_url.split("/")[-1]
                                
                                if last_video_id and last_video_id == current_video_id:
                                     should_fetch = True
                     except Exception as e:
                          logging.debug(f"[YT] Trace bot player state error: {e}")
                     
                     if should_fetch:
                          try:
                               self.bot.loop.create_task(self._fetch_autoplay_async(current_video_id))
                          except Exception:
                               threading.Thread(target=self._fetch_autoplay_sync, args=(current_video_id,), daemon=True).start()

                duration = (time.perf_counter() - start_time) * 1000
                logging.info(f"YT Get (Process) finished in {duration:.2f}ms for {title}")
                return [
                    Track(service=self.name, url=url, name=title, format=format, type=track_type, extra_info=stream, extracted_at=time.perf_counter())
                ]

    def _get_recommendations(self, video_id: str, limit: int = 5) -> List[Track]:
        try:
             logging.info(f"[YT] Fetching recommendations for {video_id}")
             url = f"https://www.youtube.com/watch?v={video_id}"
             headers = {
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
                 "Accept-Language": "en-US,en;q=0.9"
             }
             
             import httpx
             import re
             import json
             import http.cookiejar
             
             jar = None
             if self.config.cookiefile_path and os.path.isfile(self.config.cookiefile_path):
                 try:
                     jar = http.cookiejar.MozillaCookieJar(self.config.cookiefile_path)
                     jar.load(ignore_discard=True, ignore_expires=True)
                     logging.info(f"[YT] Recommendations: Loaded cookies from {self.config.cookiefile_path}")
                 except Exception as e:
                     logging.warning(f"[YT] Recommendations: Could not load cookies from {self.config.cookiefile_path}: {e}")
                     jar = None

             with httpx.Client(http2=True, follow_redirects=True, timeout=10.0, cookies=jar) as client:
                 response = client.get(url, headers=headers)
             if response.status_code != 200:
                 logging.error(f"[YT] Recommendations fetch failed: HTTP {response.status_code}")
                 return []
                 
             pattern = r"var ytInitialData = ({.*?});"
             match = re.search(pattern, response.text)
             if not match:
                 pattern = r"window\[['\"]ytInitialData['\"].*? = ({.*?});"
                 match = re.search(pattern, response.text)
                 
             if not match:
                 logging.error("[YT] Recommendations fetch failed: Could not find ytInitialData")
                 return []
                 
             data = json.loads(match.group(1))
             
             # Extract both compactVideoRenderer and lockupViewModel items
             items = []
             def find_videos_and_lockups(obj):
                 if isinstance(obj, dict):
                     if 'compactVideoRenderer' in obj:
                         items.append(('video', obj['compactVideoRenderer']))
                     elif 'lockupViewModel' in obj:
                         items.append(('lockup', obj['lockupViewModel']))
                     else:
                         for v in obj.values():
                             find_videos_and_lockups(v)
                 elif isinstance(obj, list):
                     for item in obj:
                         find_videos_and_lockups(item)
             
             try:
                 find_videos_and_lockups(data)
             except Exception as ex:
                 logging.debug(f"[YT] Recursive search error: {ex}")
             
             new_tracks = []
             count = 0
             for kind, item in items:
                  if count >= limit:
                      break
                  if not item or not isinstance(item, dict):
                      continue
                      
                  v_id = None
                  title = ""
                  channel = ""
                  
                  if kind == 'video':
                      v_id = item.get('videoId')
                      if not v_id:
                          continue
                      title_obj = item.get('title', {})
                      if 'simpleText' in title_obj:
                          title = title_obj['simpleText']
                      elif 'runs' in title_obj and isinstance(title_obj['runs'], list) and len(title_obj['runs']) > 0:
                          title = title_obj['runs'][0].get('text', '')
                          
                      channel_obj = item.get('longBylineText', {}) or item.get('shortBylineText', {})
                      if 'runs' in channel_obj and isinstance(channel_obj['runs'], list) and len(channel_obj['runs']) > 0:
                          channel = channel_obj['runs'][0].get('text', '')
                  
                  elif kind == 'lockup':
                      v_id = item.get('contentId')
                      # Filter out anything that is not a video/playlist (e.g. channels)
                      content_type = item.get('contentType')
                      if content_type != 'LOCKUP_CONTENT_TYPE_VIDEO':
                          continue
                      if not v_id:
                          continue
                      
                      metadata = item.get('metadata', {}).get('lockupMetadataViewModel', {})
                      title = metadata.get('title', {}).get('content', '')
                      
                      rows = metadata.get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
                      if len(rows) > 0:
                          parts = rows[0].get('metadataParts', [])
                          if len(parts) > 0:
                              txt_obj = parts[0].get('text', {})
                              if isinstance(txt_obj, dict):
                                  channel = txt_obj.get('content', '')
                              elif isinstance(txt_obj, str):
                                  channel = txt_obj
                  
                  if not v_id:
                      continue
                      
                  full_title = f"{title} - {channel}" if channel else title
                  
                  track = Track(
                       service=self.name,
                       name=full_title,
                       url=f"https://www.youtube.com/watch?v={v_id}",
                       type=TrackType.Dynamic,
                       extra_info=item
                  )
                  new_tracks.append(track)
                  count += 1
             
             return new_tracks
        except Exception as e:
             logging.error(f"[YT] Recommendations fetch error: {e}")
             return []

    async def _fetch_autoplay_async(self, video_id: str) -> None:
         self._fetch_autoplay_sync(video_id)

    def _fetch_autoplay_sync(self, video_id: str) -> None:
         try:
              new_tracks = self._get_recommendations(video_id, limit=5)
              if new_tracks:
                   logging.info(f"[YT] Adding {len(new_tracks)} autoplay tracks to queue")
                   self.bot.player.track_list.extend(new_tracks)
         except Exception as e:
              logging.error(f"[YT] Autoplay fetch failed: {e}")


    def search(self, query: str, limit: Optional[int] = None) -> List[Track]:
        if limit is None:
            limit = self.config.search_results
        start_time = time.perf_counter()
        # py-yt-search usage (async method)
        try:
            search_obj = VideosSearch(query, limit=limit)
            search = asyncio.run_coroutine_threadsafe(search_obj.next(), self._loop).result()
            
            # Check structure: it seems to return {'result': [Items...]}
            if search and "result" in search and search["result"]:
                tracks: List[Track] = []
                for video in search["result"]:
                    # Handle potential key differences between libraries
                    # Standard py-yt-search likely uses 'link' or 'url', or 'id'
                    # We fallback to constructing URL from ID if link is missing
                    url = video.get("link") or video.get("url")
                    if not url and video.get("id"):
                         url = f"https://www.youtube.com/watch?v={video.get('id')}"
                    
                    if not url:
                         continue

                    # Title handling
                    title = video.get("title", self.bot.translator.translate("Unknown Title"))
                    
                    track = Track(
                        service=self.name, url=url, name=title, type=TrackType.Dynamic, extra_info=None
                    )
                    tracks.append(track)
                
                if not tracks:
                     raise errors.NothingFoundError("")
                
                duration = (time.perf_counter() - start_time) * 1000
                logging.info(f"YT Search finished in {duration:.2f}ms for query: {query}")
                return tracks
            else:
                raise errors.NothingFoundError("")
        except Exception as e:
            logging.error(f"YT Search failed: {e}")
            raise errors.NothingFoundError("")

    def _connection_keeper(self):
        while True:
            time.sleep(15)
            try:
                # Run search for a minimal query to keep TCP/SSL connection warm
                self.search("music", limit=1)
            except Exception:
                pass
