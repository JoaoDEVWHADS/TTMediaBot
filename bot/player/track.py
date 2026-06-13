from __future__ import annotations
import copy
import logging
import os
from threading import Lock
from typing import Any, Dict, Optional, TYPE_CHECKING

from bot.player.enums import TrackType
from bot import utils

if TYPE_CHECKING:
    from bot.services import Service


class Track:
    format: str
    type: TrackType

    def __init__(
        self,
        service: str = "",
        url: str = "",
        name: str = "",
        format: str = "",
        extra_info: Optional[Dict[str, Any]] = None,
        type: TrackType = TrackType.Default,
    ) -> None:
        self.service = service
        self.url = url
        self.name = name
        self.format = format
        self.extra_info = extra_info
        self.type = type
        self._lock = Lock()
        self._is_fetched = False
        self._fetch_failed = False

    def download(self, directory: str, video: bool = False) -> str:
        service: Service = get_service_by_name(self.service)
        format = self.format if not video else "mp4"
        file_name = self.name + "." + format
        file_name = utils.clean_file_name(file_name)
        file_path = os.path.join(directory, file_name)
        service.download(self, file_path, video=video)
        return file_path

    def _fetch_stream_data(self):
        if self.type != TrackType.Dynamic or self._is_fetched or self._fetch_failed:
            return
        self._original_track = copy.deepcopy(self)
        service: Service = get_service_by_name(self.service)
        try:
            track = service.get(self._url, extra_info=self.extra_info, process=True)[0]
        except Exception as e:
            logging.error(f"Failed to fetch stream data for '{self._name or self._url}': {e}")
            self._fetch_failed = True
            raise
        self.url = track.url
        self.name = track.name
        self._original_track.name = track.name
        self.format = track.format
        self.type = track.type
        self.extra_info = track.extra_info
        self._is_fetched = True

    @property
    def url(self) -> str:
        with self._lock:
            self._fetch_stream_data()
            return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    @property
    def name(self) -> str:
        with self._lock:
            if not self._name:
                self._fetch_stream_data()
            return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    def get_meta(self) -> Dict[str, Any]:
        try:
            return {"name": self.name, "url": self.url}
        except:
            return {"name": None, "url": ""}

    def get_raw(self) -> Track:
        if hasattr(self, "_original_track"):
            return self._original_track
        else:
            return self

    def __bool__(self):
        if self.service or self.url:
            return True
        else:
            return False

    def __getstate__(self) -> Dict[str, Any]:
        state: Dict[str, Any] = self.__dict__.copy()
        del state["_lock"]
        return state

    def __setstate__(self, state: Dict[str, Any]):
        self.__dict__.update(state)
        self._lock = Lock()
