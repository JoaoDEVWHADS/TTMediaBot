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

    def initialize(self):
        self._ydl_config = {
            "skip_download": True,
            "format": "bestaudio/best",
            # Performance optimizations:
            "format_sort": ["res:144", "codec:mp3", "codec:m4a", "codec:opus"], # Prioritize mp3/m4a for simplicity
            "youtube_include_dash_manifest": False, # Skip DASH manifest download
            "youtube_include_hls_manifest": False,  # Skip HLS manifest download
            "socket_timeout": 5,
            "logger": logging.getLogger("root"),
            "js_runtimes": {"node": {}},
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
            "check_formats": False, # Skip extra network request for format validation
            "noplaylist": True,    # Ensure we don't accidentally load playlists
        }

        # Persistent event loop for faster async operations
        self._loop = asyncio.new_event_loop()
        threading.Thread(target=self._loop.run_forever, daemon=True).start()

        # Pre-warming: establishing connections early
        threading.Thread(target=self._pre_warm, daemon=True).start()

    def _pre_warm(self):
        try:
            # Establish initial connections to YouTube
            logging.info("YT Service pre-warming...")
            self.search("music")
            logging.info("YT Service pre-warming finished.")
        except Exception as e:
            logging.debug(f"YT Pre-warming failed: {e}")

    @contextmanager
    def _temp_cookie_file(self) -> Generator[Optional[str], None, None]:
        if not self.config.cookiefile_path or not os.path.isfile(self.config.cookiefile_path):
            yield None
            return

        # Unique name per thread/process to avoid collisions
        temp_cookie_path = os.path.join(
            tempfile.gettempdir(), 
            f"yt_cookies_{os.getpid()}_{threading.get_ident()}.txt"
        )
        
        try:
            shutil.copy2(self.config.cookiefile_path, temp_cookie_path)
            yield temp_cookie_path
        finally:
            if os.path.isfile(temp_cookie_path):
                try:
                    os.remove(temp_cookie_path)
                except Exception as e:
                    logging.debug(f"Failed to remove temp cookie file {temp_cookie_path}: {e}")
            
    def download(self, track: Track, file_path: str) -> None:
        start_time = time.perf_counter()
        info = track.extra_info
        if not info:
            super().download(track, file_path)
            duration = (time.perf_counter() - start_time) * 1000
            logging.info(f"YT Download finished in {duration:.2f}ms for {track.name}")
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
                dl = get_suitable_downloader(info)(ydl, config)
                dl.download(file_path, info)

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
        
        # Instantiate per request for thread safety
        config = self._ydl_config.copy()
        with self._temp_cookie_file() as cookie_file:
            if cookie_file:
                config["cookiefile"] = cookie_file
            
            with YoutubeDL(config) as ydl:
                if not extra_info:
                    info = ydl.extract_info(url, process=False)
                else:
                    info = extra_info
                
                info_type = None
                if "_type" in info:
                    info_type = info["_type"]
                if info_type == "url" and not info["ie_key"]:
                    return self.get(info["url"], process=False)
                elif info_type == "playlist":
                    tracks: List[Track] = []
                    for entry in info["entries"]:
                        data = self.get("", extra_info=entry, process=False)
                        tracks += data
                    duration = (time.perf_counter() - start_time) * 1000
                    logging.info(f"YT Get (Playlist) finished in {duration:.2f}ms for {url}")
                    return tracks
                if not process:
                    duration = (time.perf_counter() - start_time) * 1000
                    logging.info(f"YT Get (No Process) finished in {duration:.2f}ms for {url}")
                    return [
                        Track(service=self.name, extra_info=info, type=TrackType.Dynamic)
                    ]
                try:
                    stream = ydl.process_ie_result(info)
                except Exception:
                    raise errors.ServiceError()
                
                if "url" in stream:
                    url = stream["url"]
                else:
                    raise errors.ServiceError()
                title = stream["title"]
                if "uploader" in stream:
                    title += " - {}".format(stream["uploader"])
                format = "mp3"
                if "is_live" in stream and stream["is_live"]:
                    track_type = TrackType.Live
                else:
                    track_type = TrackType.Default
                
                duration = (time.perf_counter() - start_time) * 1000
                logging.info(f"YT Get (Process) finished in {duration:.2f}ms for {title}")
                return [
                    Track(service=self.name, url=url, name=title, format=format, type=track_type, extra_info=stream)
                ]

    def search(self, query: str) -> List[Track]:
        start_time = time.perf_counter()
        # py-yt-search usage (async method)
        try:
            # The library is designed to be async. using .result() might be synchronous wrapper 
            # but using .next() via asyncio.run is safer as per examples.
            search_obj = VideosSearch(query, limit=10)
            search = asyncio.run(search_obj.next())
            
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
                    title = video.get("title", "Unknown Title")
                    
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
