from __future__ import annotations
import logging
import time
import asyncio
import threading
import os
import json
import http.cookiejar
import shutil
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from bot import Bot

from yt_dlp import YoutubeDL
from yt_dlp.downloader import get_suitable_downloader
from ytmusicapi import YTMusic

from bot.config.models import YtmModel
from bot.player.enums import TrackType
from bot.player.track import Track
from bot.services import Service as _Service
from bot import errors


class YtmService(_Service):
    def __init__(self, bot: Bot, config: YtmModel):
        self.bot = bot
        self.config = config
        self.name = "ytm"
        self.hostnames = []
        self.is_enabled = self.config.enabled
        self.error_message = ""
        self.warning_message = ""
        self.help = ""
        self.hidden = False
        self.ytmusic = None
        # Access config directly to avoid circular dependency with service_manager
        self.yt_config = bot.config.services.yt
        
    def _fetch_and_queue_autoplay(self, video_id: str, original_url: str):
        """Background task to fetch Watch Playlist and add to queue."""
        try:
            logging.info(f"[YTM] Starting background Autoplay fetch for video_id={video_id}")
            start_time = time.perf_counter()
            
            # radio=False ensures we get the "Up Next" / Autoplay queue
            watch_playlist = self.ytmusic_public.get_watch_playlist(videoId=video_id, limit=50, radio=False)
            tracks_data = watch_playlist.get("tracks", [])
            
            new_tracks: List[Track] = []
            # Skip the first track usually as it is the current one, BUT get_watch_playlist 
            # might return the current one as first item.
            # We want to add RECOMMENDATIONS to the queue.
            # If the first item is the same video_id, skip it.
            
            for item in tracks_data:
                t_video_id = item.get("videoId")
                if t_video_id == video_id:
                    continue
                    
                t_title = item.get("title")
                t_artist = ""
                if "artists" in item:
                     t_artist = ", ".join([a["name"] for a in item["artists"]])
                
                full_title = f"{t_title} - {t_artist}" if t_artist else t_title
                # Optimization: Use www.youtube.com for faster extraction later
                t_url = f"https://www.youtube.com/watch?v={t_video_id}"
                
                new_tracks.append(
                     Track(service=self.name, url=t_url, name=full_title, type=TrackType.Dynamic, extra_info=item)
                )
            
            if new_tracks:
                # Add to bot queue safely
                self.bot.player.track_list.extend(new_tracks)
                
                duration = (time.perf_counter() - start_time) * 1000
                logging.info(f"[YTM] Background Autoplay fetch added {len(new_tracks)} tracks in {duration:.2f}ms")
            else:
                logging.info("[YTM] Background Autoplay fetch found no new tracks.")
                
        except Exception as e:
            logging.error(f"[YTM] Background Autoplay fetch failed: {e}")

    def initialize(self):
        # Initialize YTMusic with cookies if available
        cookie_path = None
        if self.yt_config and self.yt_config.cookiefile_path:
             cookie_path = self.yt_config.cookiefile_path

        self.cookiejar = None
        auth = None
        if cookie_path and os.path.isfile(cookie_path):
             try:
                 # Parse Netscape cookies to build a Cookie header
                 self.cookiejar = http.cookiejar.MozillaCookieJar(cookie_path)
                 self.cookiejar.load(ignore_discard=True, ignore_expires=True)
                 
                 cookie_header_parts = []
                 sapisid = ""
                 for cookie in self.cookiejar:
                     if "youtube" in cookie.domain or "google" in cookie.domain:
                         cookie_header_parts.append(f"{cookie.name}={cookie.value}")
                     if cookie.name == "SAPISID":
                         sapisid = cookie.value
                 
                 if cookie_header_parts:
                     # 1. Extract cookies to string
                     cookie_string = "; ".join(cookie_header_parts)
                     
                     # 3. Construct headers dict
                     headers = {
                         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
                         "accept-language": "en-US",
                         "content-type": "application/json",
                         "cookie": cookie_string,
                         "accept": "*/*",
                         "x-goog-authuser": "0",
                         "x-origin": "https://music.youtube.com"
                     }
                     
                     # 4. Generate Authorization header if SAPISID is available
                     if sapisid:
                         try:
                             from ytmusicapi.helpers import get_authorization
                             auth_header = get_authorization(sapisid + " " + "https://music.youtube.com")
                             headers["authorization"] = auth_header
                         except ImportError:
                             import hashlib
                             timestamp = str(int(time.time()))
                             payload = f"{timestamp} {sapisid} https://music.youtube.com"
                             sha = hashlib.sha1(payload.encode("utf-8")).hexdigest()
                             headers["authorization"] = f"SAPISIDHASH {timestamp}_{sha}"
                     
                     auth = headers
             except Exception as e:
                 logging.error(f"Failed to parse cookies for YTM: {e}")

        if auth and isinstance(auth, dict) and "authorization" in auth:
             self.ytmusic = YTMusic(auth=auth)
        else:
             # Fallback to public instance if auth generation failed
             self.ytmusic = YTMusic()
        
        # Explicit public instance for search/metadata (User Request: No cookies for search)
        self.ytmusic_public = YTMusic()

        # Persistent event loop for safer async operations if needed
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        self._ydl_config = {
            "skip_download": True,
            "format": "bestaudio/best",
            "format_sort": ["res:144", "codec:mp3", "codec:m4a", "codec:opus"],
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
            "socket_timeout": 5,
            "logger": logging.getLogger("root"),
            "js_runtimes": {"node": {}},
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "check_formats": False, # Skip extra network request for format validation
            "noplaylist": True,    # Ensure we don't accidentally load playlists
            "extract_flat": "in_playlist",
        }

        # Pre-warming for YTM
        threading.Thread(target=self._pre_warm, daemon=True).start()

    def _pre_warm(self):
        try:
            logging.info("YTM Service pre-warming...")
            # Establish initial connection to YTM
            self.ytmusic_public.search("music", filter="songs", limit=1)
            logging.info("YTM Service pre-warming finished.")
        except Exception as e:
            logging.debug(f"YTM Pre-warming failed: {e}")

    @contextmanager
    def _temp_cookie_file(self) -> Generator[Optional[str], None, None]:
        if not self.yt_config.cookiefile_path or not os.path.isfile(self.yt_config.cookiefile_path):
            yield None
            return

        # Unique name per thread/process to avoid collisions
        temp_cookie_path = os.path.join(
            tempfile.gettempdir(), 
            f"ytm_cookies_{os.getpid()}_{threading.get_ident()}.txt"
        )
        
        try:
            shutil.copy2(self.yt_config.cookiefile_path, temp_cookie_path)
            yield temp_cookie_path
        finally:
            if os.path.isfile(temp_cookie_path):
                try:
                    os.remove(temp_cookie_path)
                except Exception as e:
                    logging.debug(f"Failed to remove temp cookie file {temp_cookie_path}: {e}")

    def download(self, track: Track, file_path: str) -> None:
        start_time = time.perf_counter()
        # Re-use YT Service logic or bare extraction
        # Since implementation plan said re-use logic:
        info = track.extra_info
        if not info:
             super().download(track, file_path)
             duration = (time.perf_counter() - start_time) * 1000
             logging.info(f"YTM Download finished in {duration:.2f}ms for {track.name}")
             return
        
        # Instantiate per request for thread safety
        config = self._ydl_config.copy()
        config["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

        with self._temp_cookie_file() as cookie_file:
             if cookie_file:
                  config["cookiefile"] = cookie_file
             with YoutubeDL(config) as ydl:
                  # We need to ensure skip_download is False for actual downloading
                  ydl.params['skip_download'] = False
                  dl = get_suitable_downloader(info)(ydl, config)
                  dl.download(file_path, info)

        duration = (time.perf_counter() - start_time) * 1000
        logging.info(f"YTM Download finished in {duration:.2f}ms for {track.name}")

    def get(
        self,
        url: str,
        extra_info: Optional[Dict[str, Any]] = None,
        process: bool = False,
    ) -> List[Track]:
        start_time = time.perf_counter()
        if not (url or extra_info):
            raise errors.InvalidArgumentError()

        # If process=True, we are likely in the player trying to resolve the stream URL
        if process:
             # Instantiate per request for thread safety
             config = self._ydl_config.copy()
             with self._temp_cookie_file() as cookie_file:
                  if cookie_file:
                       config["cookiefile"] = cookie_file
                  
                  with YoutubeDL(config) as ydl:
                       # If we have extra_info, use it, otherwise extract from URL
                       if extra_info:
                            info = extra_info
                            if "url" not in info and "videoId" in info:
                                 # Construct URL for yt-dlp
                                 # Optimization: Use www.youtube.com instead of music.youtube.com for faster extraction
                                 url = f"https://www.youtube.com/watch?v={info['videoId']}"
                                 info = ydl.extract_info(url, process=False)
                       else:
                            info = ydl.extract_info(url, process=False)
                       
                       # Process stream
                       stream = ydl.process_ie_result(info)
                       if "url" in stream:
                            url = stream["url"]
                       else:
                            raise errors.ServiceError()
                       
                       title = stream.get("title", "Unknown")
                       if "uploader" in stream:
                            title += " - {}".format(stream["uploader"])
                       format = "mp3"
                       
                       duration = (time.perf_counter() - start_time) * 1000
                       logging.info(f"YTM Get (Process) finished in {duration:.2f}ms for {title}")
                  
                  # TRIGGER BACKGROUND AUTOPLAY FETCH
                  current_video_id = None
                  if extra_info and "videoId" in extra_info:
                       current_video_id = extra_info["videoId"]
                  elif "id" in stream:
                       current_video_id = stream["id"]
                  
                  if current_video_id:
                       should_fetch = False
                       try:
                            if self.bot.player.track_list:
                                 last_track = self.bot.player.track_list[-1]
                                 last_video_id = None
                                 if last_track.extra_info and 'videoId' in last_track.extra_info:
                                      last_video_id = last_track.extra_info.get('videoId')
                                 
                                 if last_video_id and last_video_id == current_video_id:
                                      should_fetch = True
                                      logging.info(f"[YTM] Autoplay trigger: Current track IS last track (ID match: {current_video_id})")
                                 elif last_track.url == url:
                                      should_fetch = True
                                      logging.info(f"[YTM] Autoplay trigger: Current track IS last track (URL match)")
                       except Exception as e:
                            logging.debug(f"[YTM] Trace bot player state error: {e}")
                       
                       if should_fetch:
                            try:
                                 self.bot.loop.create_task(self._fetch_autoplay_async(current_video_id))
                            except Exception:
                                 threading.Thread(target=self._fetch_autoplay_sync, args=(current_video_id,), daemon=True).start()
                  
                  return [
                       Track(
                            service=self.name,
                            name=title,
                            url=url,
                            type=TrackType.Default,
                            format=format,
                            extra_info=stream,
                       )
                  ]

        # If process=False, we are adding to queue (The "Radio" logic)
        video_id = None
        if extra_info and "videoId" in extra_info:
             video_id = extra_info["videoId"]
        elif url:
             if "v=" in url:
                  video_id = url.split("v=")[1].split("&")[0]
             elif "youtu.be" in url:
                  video_id = url.split("/")[-1]
        
        if not video_id:
             return [Track(service=self.name, url=url, type=TrackType.Dynamic)]

        # 2. Get Watch Playlist (Autoplay)
        try:
             watch_playlist = self.ytmusic_public.get_watch_playlist(videoId=video_id, limit=20, radio=False)
             tracks_data = watch_playlist.get("tracks", [])
             
             new_tracks: List[Track] = []
             for item in tracks_data:
                  t_title = item.get("title")
                  t_artist = ""
                  if "artists" in item:
                       t_artist = ", ".join([a["name"] for a in item["artists"]])
                  
                  full_title = f"{t_title} - {t_artist}" if t_artist else t_title
                  t_video_id = item.get("videoId")
                  t_url = f"https://www.youtube.com/watch?v={t_video_id}"
                  
                  new_tracks.append(
                       Track(service=self.name, url=t_url, name=full_title, type=TrackType.Dynamic, extra_info=item)
                  )
             
             duration = (time.perf_counter() - start_time) * 1000
             logging.info(f"YTM Get (Watch Playlist) finished in {duration:.2f}ms for video_id {video_id}")
             return new_tracks

        except Exception as e:
             logging.error(f"YTM Watch Playlist failed: {e}")
             duration = (time.perf_counter() - start_time) * 1000
             logging.info(f"YTM Get (Fallback) finished in {duration:.2f}ms for {url}")
             return [Track(service=self.name, url=url, type=TrackType.Dynamic)]

    async def _fetch_autoplay_async(self, video_id: str) -> None:
         self._fetch_autoplay_sync(video_id)

    def _fetch_autoplay_sync(self, video_id: str) -> None:
         try:
              logging.info(f"[YTM] Fetching autoplay for {video_id}")
              watch_playlist = self.ytmusic_public.get_watch_playlist(videoId=video_id, limit=5)
              
              if 'tracks' in watch_playlist:
                   new_tracks = []
                   for t_info in watch_playlist['tracks'][1:]:
                        title = t_info['title']
                        if 'artists' in t_info:
                             artists = ", ".join([a['name'] for a in t_info['artists']])
                             title += f" - {artists}"
                        
                        v_id = t_info['videoId']
                        track = Track(
                             service=self.name,
                             name=title,
                             url=f"https://www.youtube.com/watch?v={v_id}",
                             type=TrackType.Dynamic,
                             extra_info=t_info
                        )
                        new_tracks.append(track)
                   
                   if new_tracks:
                        logging.info(f"[YTM] Adding {len(new_tracks)} autoplay tracks to queue")
                        self.bot.player.track_list.extend(new_tracks)
         except Exception as e:
              logging.error(f"[YTM] Autoplay fetch failed: {e}")

    def search(self, query: str) -> List[Track]:
        start_time = time.perf_counter()
        results = self.ytmusic_public.search(query, filter="songs", limit=1)
        if not results:
             raise errors.NothingFoundError("")
        
        results = results[:1]
        
        duration = (time.perf_counter() - start_time) * 1000
        logging.info(f"YTM Search (Fast) finished in {duration:.2f}ms for query: {query}")
        
        return self._create_tracks_from_results(results)

    def _create_tracks_from_results(self, results: List[Dict[str, Any]]) -> List[Track]:
        tracks: List[Track] = []
        for item in results:
             t_title = item.get("title")
             t_artist = ""
             if "artists" in item:
                  t_artist = ", ".join([a["name"] for a in item["artists"]])
             
             full_title = f"{t_title} - {t_artist}" if t_artist else t_title
             t_video_id = item.get("videoId")
             t_url = f"https://www.youtube.com/watch?v={t_video_id}"
             
             tracks.append(
                  Track(service=self.name, url=t_url, name=full_title, type=TrackType.Dynamic, extra_info=item)
             )
        return tracks
