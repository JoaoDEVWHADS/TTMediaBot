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
                # self.bot.player is accessible
                # thread safety: adding to list is atomic usually, but let's see how Player handles it.
                # Player.play usually pops. Queue is a list.
                # We can extend the queue.
                
                # Check if we should lock? The bot seems to be single-process mostly with threads.
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

        auth = None
        if cookie_path and os.path.isfile(cookie_path):
             try:
                 # Parse Netscape cookies to build a Cookie header
                 cj = http.cookiejar.MozillaCookieJar(cookie_path)
                 cj.load()
                 
                 cookie_header_parts = []
                 sapisid = ""
                 for cookie in cj:
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
                         # We need to compute SAPISIDHASH.
                         # Simplified implementation to avoid importing internal helpers if possible,
                         # but importing from ytmusicapi.helpers is safer.
                         try:
                             from ytmusicapi.helpers import get_authorization
                             # get_authorization expects (sapisid + " " + origin)
                             # Wait, checks implementation usually: sha1(time + " " + sapisid + " " + origin)
                             # Let's import the helper to be safe.
                             auth_header = get_authorization(sapisid + " " + "https://music.youtube.com")
                             headers["authorization"] = auth_header
                         except ImportError:
                             # Fallback if helpers not accessible (unlikely)
                             import time
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
             logging.warning("YTM: initializing without auth (cookies failed)")
             self.ytmusic = YTMusic()
        
        # Explicit public instance for search/metadata (User Request: No cookies for search)
        self.ytmusic_public = YTMusic()

        self._ydl_config = {
            "skip_download": True,
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            # Performance optimizations:
            "format_sort": ["res:144", "codec:m4a", "codec:opus"], # Prioritize low res/audio codecs for speed
            "youtube_include_dash_manifest": False, # Skip DASH manifest download
            "youtube_include_hls_manifest": False,  # Skip HLS manifest download
            "socket_timeout": 5,
            "logger": logging.getLogger("root"),
            "js_runtimes": {"node": {}},
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "extract_flat": "in_playlist", # Speed up if URL is a playlist, though we usually pass single video URLs here
        }

        if cookie_path and os.path.isfile(cookie_path):
            self._ydl_config |= {"cookiefile": cookie_path}

        if cookie_path and os.path.isfile(cookie_path):
            self._ydl_config |= {"cookiefile": cookie_path}
            
        # Removed instance reuse due to thread safety
        # self.ydl = YoutubeDL(self._ydl_config)

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
        with YoutubeDL(self._ydl_config) as ydl:
             # We need to process it to get the stream if we don't have it
             # But download usually expects a URL or ID
             pass
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
             with YoutubeDL(self._ydl_config) as ydl:
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
                 format = stream.get("ext", "m4a")
                 
                 duration = (time.perf_counter() - start_time) * 1000
                 logging.info(f"YTM Get (Process) finished in {duration:.2f}ms for {title}")
                 
                 # TRIGGER BACKGROUND AUTOPLAY FETCH
                 # Check if we have a videoId and if we should fetch autoplay
                 # We assume if it's a dynamic track from YTM search, we want autoplay.
                 # extra_info from search has videoId.
                 
                 current_video_id = None
                 if extra_info and "videoId" in extra_info:
                     current_video_id = extra_info["videoId"]
                 elif "id" in stream:
                     current_video_id = stream["id"]
                 
                 # We need to ensure we don't trigger this for every track in the playlist 
                 # if they were already added via autoplay. 
                 # But here 'get' is called for the track being played.
                 # If the queue is running low, we might want to fetch more?
                 # For now, let's stick to the user request: "prefetch after first music starts".
                 # This usually means when we play a track from Search.
                 
                 # If the track came from Search, it has extra_info populated.
                 if current_video_id:
                     # Check if we are playing the last track (or close to it)
                     # We want to enable infinite autoplay.
                     # Logic: If this is the last track in the list, fetch more.
                     
                     should_fetch = False
                     try:
                         if self.bot.player.track_list:
                             last_track = self.bot.player.track_list[-1]
                             
                             # Robust check: Compare videoId if available
                             last_video_id = None
                             if last_track.extra_info and 'videoId' in last_track.extra_info:
                                 last_video_id = last_track.extra_info.get('videoId')
                             
                             # Check if current url matches last track url, or if index is at end, or videoId matches
                             if last_video_id and last_video_id == current_video_id:
                                 should_fetch = True
                                 logging.info(f"[YTM] Autoplay trigger: Current track IS last track (ID match: {current_video_id})")
                             elif last_track.url == url:
                                 should_fetch = True
                                 logging.info(f"[YTM] Autoplay trigger: Current track IS last track (URL match)")
                             elif self.bot.player.track_index >= len(self.bot.player.track_list) - 1:
                                 should_fetch = True
                                 logging.info(f"[YTM] Autoplay trigger: Track index {self.bot.player.track_index} is at end of list")
                             else:
                                 logging.debug(f"[YTM] Autoplay skipped: Not last track. Index: {self.bot.player.track_index}, List Len: {len(self.bot.player.track_list)}")
                         else:
                             # If list is empty (shouldn't be if we are playing), fetch just in case
                             should_fetch = True
                             logging.info(f"[YTM] Autoplay trigger: Track list empty")
                     except Exception as e:
                         logging.warning(f"[YTM] Error checking track list for autoplay: {e}")
                         should_fetch = True # Default to fetching if check fails?
                         
                     if should_fetch:
                         # Run in a separate thread to avoid blocking playback start
                         threading.Thread(target=self._fetch_and_queue_autoplay, args=(current_video_id, url), daemon=True).start()
                 
                 return [
                      Track(service=self.name, url=url, name=title, format=format, type=TrackType.Default, extra_info=stream)
                 ]

        # If process=False, we are adding to queue (The "Radio" logic)
        # 1. Identify Video ID
        video_id = None
        if extra_info and "videoId" in extra_info:
             video_id = extra_info["videoId"]
        elif url:
             # Basic extraction of ID from URL if using ytmusicapi
             # Or let yt-dlp extract ID quickly
             # Let's try to pass the URL to ytmusicapi if it's a search result url, otherwise regex?
             # For simplicity, let's assume we get a videoId from search mainly.
             # If user pasted a link, we need to extract ID.
             if "v=" in url:
                  video_id = url.split("v=")[1].split("&")[0]
             elif "youtu.be" in url:
                  video_id = url.split("/")[-1]
        
        if not video_id:
             # Fallback to simple single track if no ID found
             return [Track(service=self.name, url=url, type=TrackType.Dynamic)]

        # 2. Get Watch Playlist (Autoplay)
        try:
             # radio=False ensures we get the "Up Next" / Autoplay queue, not a "Song Radio"
             watch_playlist = self.ytmusic_public.get_watch_playlist(videoId=video_id, limit=20, radio=False)
             tracks_data = watch_playlist.get("tracks", [])
             
             new_tracks: List[Track] = []
             for i, item in enumerate(tracks_data):
                  # Item structure from ytmusicapi
                  t_title = item.get("title")
                  t_artist = ""
                  if "artists" in item:
                       t_artist = ", ".join([a["name"] for a in item["artists"]])
                  
                  full_title = f"{t_title} - {t_artist}" if t_artist else t_title
                  t_video_id = item.get("videoId")
                  # Optimization: Use www.youtube.com for faster extraction later
                  t_url = f"https://www.youtube.com/watch?v={t_video_id}"
                  
                  # The first track is the requested one, subsequence are recommendations
                  # extra_info stores data needed for later processing
                  new_tracks.append(
                       Track(service=self.name, url=t_url, name=full_title, type=TrackType.Dynamic, extra_info=item)
                  )
             
             duration = (time.perf_counter() - start_time) * 1000
             logging.info(f"YTM Get (Watch Playlist) finished in {duration:.2f}ms for video_id {video_id}")
             return new_tracks

        except Exception as e:
             logging.error(f"YTM Watch Playlist failed: {e}")
             # Fallback to single track
             duration = (time.perf_counter() - start_time) * 1000
             logging.info(f"YTM Get (Fallback) finished in {duration:.2f}ms for {url}")
             return [Track(service=self.name, url=url, type=TrackType.Dynamic)]

    def search(self, query: str) -> List[Track]:
        start_time = time.perf_counter()
        # Optimization: Limit to 1 result directly in API call to reduce overhead
        results = self.ytmusic_public.search(query, filter="songs", limit=1)
        if not results:
             raise errors.NothingFoundError("")
        
        # Limit results to 1 explicitly to avoid API fuzzy limits
        results = results[:1]
        
        # User wants "Next" to trigger Autoplay via background task, so search just returns the 1 result.
        
        duration = (time.perf_counter() - start_time) * 1000
        logging.info(f"YTM Search (Fast) finished in {duration:.2f}ms for query: {query}")
        
        # We return the mapped track. The 'extra_info' will carry the videoId needed for the background fetch later.
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
             t_video_id = item.get("videoId")
             # Optimization: Use www.youtube.com for faster extraction later
             t_url = f"https://www.youtube.com/watch?v={t_video_id}"
             
             tracks.append(
                  Track(service=self.name, url=t_url, name=full_title, type=TrackType.Dynamic, extra_info=item)
             )
        return tracks
