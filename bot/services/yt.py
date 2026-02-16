from __future__ import annotations
import logging
import time
import os
import asyncio
import shutil
import tempfile
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
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            # Performance optimizations:
            "format_sort": ["res:144", "codec:m4a", "codec:opus"], # Prioritize low res/audio codecs for speed
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
        }

        if self.config.cookiefile_path and os.path.isfile(self.config.cookiefile_path):
            self._ydl_config |= {"cookiefile": self.config.cookiefile_path}
            
    def download(self, track: Track, file_path: str) -> None:
        start_time = time.perf_counter()
        info = track.extra_info
        if not info:
            super().download(track, file_path)
            duration = (time.perf_counter() - start_time) * 1000
            logging.info(f"YT Download finished in {duration:.2f}ms for {track.name}")
            return
        
        # Instantiate per request for thread safety, but use shared config (no file copy)
        with YoutubeDL(self._ydl_config) as ydl:
            dl = get_suitable_downloader(info)(ydl, self._ydl_config)
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
        
        # Instantiate per request for thread safety, but use shared config (no file copy)
        with YoutubeDL(self._ydl_config) as ydl:
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
            format = stream["ext"]
            if "is_live" in stream and stream["is_live"]:
                type = TrackType.Live
            else:
                type = TrackType.Default
            
            duration = (time.perf_counter() - start_time) * 1000
            logging.info(f"YT Get (Process) finished in {duration:.2f}ms for {title}")
            return [
                Track(service=self.name, url=url, name=title, format=format, type=type, extra_info=stream)
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
