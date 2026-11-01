from __future__ import annotations
import html
import logging
import time
import threading
from typing import Any, Dict, Callable, List, Optional, TYPE_CHECKING
import random

import mpv

from bot import errors
from bot.player.enums import Mode, State, TrackType
from bot.player.track import Track
from bot.player.queue_manager import QueueManager
from bot.sound_devices import SoundDevice, SoundDeviceType


if TYPE_CHECKING:
    from bot import Bot


PREFETCH_DELAY_SECONDS = 0.05


class Player:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = bot.config.player
        self.cache = bot.cache
        self.cache_manager = bot.cache_manager
        mpv_options = {
            "ao": "pulse",
            "audio_samplerate": 48000,
            "audio_channels": "stereo",
            "audio_format": "s16",
            "gapless_audio": "yes",
            "cache": "yes",
            "cache_secs": 30,
            "demuxer_max_bytes": 16777216,
            "demuxer_max_back_bytes": 8388608,
            "demuxer_readahead_secs": 20,
            "stream_buffer_size": 131072,
            "network_timeout": 30,
            "video": False,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "ytdl": False,
        }
        mpv_options.update(self.config.player_options)
        self._default_user_agent = mpv_options.get("user_agent", "")
        try:
            self._player = mpv.MPV(**mpv_options, log_handler=self.log_handler)
        except AttributeError:
            del mpv_options["demuxer_max_back_bytes"]
            self._player = mpv.MPV(**mpv_options, log_handler=self.log_handler)
        self._log_level = 5
        self._current_user_agent: Optional[str] = None
        self._current_header_fields: Optional[List[str]] = None
        self.track_list: List[Track] = []
        self.track: Track = Track()
        self.track_index: int = -1
        self.state = State.Stopped
        self.mode = Mode.TrackList
        self.volume = self.config.default_volume
        self.is_playlist: bool = False
        self._navigation_lock = threading.RLock()
        self._playback_trace_lock = threading.Lock()
        self._playback_trace_counter = 0
        self._playback_trace: Dict[str, Any] = {}
        self._pending_playback_context: Dict[str, Any] = {}
        self._prefetch_lock = threading.Lock()
        self._prefetch_timer_lock = threading.Lock()
        self._prefetch_timer: Optional[threading.Timer] = None

        self.queue: QueueManager = QueueManager()

    def initialize(self) -> None:
        logging.debug("Initializing player")
        logging.debug("Player initialized")

    def run(self) -> None:
        logging.debug("Registering player callbacks")
        self.register_event_callback("end-file", self.on_end_file)
        for event_name in (
            "start-file",
            "file-loaded",
            "audio-reconfig",
            "playback-restart",
        ):
            self._register_playback_timing_event(event_name)
        self._player.observe_property("metadata", self.on_metadata_update)
        self._player.observe_property("media-title", self.on_metadata_update)
        logging.debug("Player callbacks registered")

    def close(self) -> None:
        logging.debug("Closing player")
        self._cancel_prefetch()
        if self.state != State.Stopped:
            self.stop()
        self._player.terminate()
        logging.debug("Player closed")

    def play(
        self,
        tracks: Optional[List[Track]] = None,
        start_track_index: Optional[int] = None,
        is_playlist: Optional[bool] = None,
        timing_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if tracks != None:
            self.track_list = tracks
            if is_playlist is not None:
                self.is_playlist = is_playlist
            else:
                self.is_playlist = len(tracks) > 1
            if not start_track_index and self.mode == Mode.Random:
                self.shuffle(True)
                self.track_index = self._index_list[0]
                self.track = self.track_list[self.track_index]
            else:
                self.track_index = start_track_index if start_track_index else 0
                self.track = tracks[self.track_index]
            self._pending_playback_context = timing_context or {}
            self._play(self.track.url)
        else:
            self._player.pause = False
        self._player.volume = self.volume
        self.state = State.Playing

    def pause(self) -> None:
        self.state = State.Paused
        self._player.pause = True

    def stop(self) -> None:
        self._cancel_prefetch()
        self.state = State.Stopped
        self._player.stop()
        self.track_list = []
        self.track = Track()
        self.track_index = -1
        self.is_playlist = False

    def _play(self, arg: str, save_to_recents: bool = True) -> None:
        trace = self._start_playback_trace()
        if save_to_recents:
            try:
                if 0 <= self.track_index < len(self.track_list):
                    track_raw = self.track_list[self.track_index].get_raw()
                    if not self.cache.recents or self.cache.recents[-1] != track_raw:
                        self.cache.recents.append(track_raw)
                        self.cache_manager.save()
            except Exception as e:
                logging.debug(f"[Player] Failed to save recents: {e}")
            
        # Apply headers dynamically if available in extra_info only when changed
        extra_info = getattr(self.track, "extra_info", None) or {}
        headers = extra_info.get("http_headers", {})
        target_ua = headers.get("User-Agent") if headers else self._default_user_agent
        target_headers = [
            f"{key}: {value}"
            for key, value in headers.items()
            if key.lower() != "user-agent"
        ]

        if self._current_user_agent != target_ua:
            try:
                self._player.user_agent = target_ua
                self._current_user_agent = target_ua
                logging.debug("[Player] HTTP User-Agent applied to MPV")
            except Exception as e:
                logging.debug(f"[Player] Failed to apply User-Agent to MPV: {e}")

        if self._current_header_fields != target_headers:
            try:
                self._player.http_header_fields = target_headers
                self._current_header_fields = target_headers
                logging.debug("[Player] HTTP headers applied to MPV")
            except Exception as e:
                logging.debug(f"[Player] Failed to apply HTTP headers to MPV: {e}")
                
        self._player.pause = False
        self._player.play(arg)
        self._log_playback_timing("mpv_play_submitted", trace)
        self._schedule_prefetch()

    def _schedule_prefetch(self) -> None:
        with self._prefetch_timer_lock:
            if self._prefetch_timer is not None:
                self._prefetch_timer.cancel()
            timer = threading.Timer(
                PREFETCH_DELAY_SECONDS,
                self._prefetch_next_track,
            )
            timer.daemon = True
            self._prefetch_timer = timer
            timer.start()

    def _cancel_prefetch(self) -> None:
        with self._prefetch_timer_lock:
            if self._prefetch_timer is not None:
                self._prefetch_timer.cancel()
                self._prefetch_timer = None

    def _start_playback_trace(self) -> Dict[str, Any]:
        with self._playback_trace_lock:
            self._playback_trace_counter += 1
            timing_context = self._pending_playback_context
            self._pending_playback_context = {}
            trace = {
                "id": self._playback_trace_counter,
                "started_at": time.perf_counter(),
                "track": self.track.name or "Unknown",
                "service": self.track.service or "unknown",
                "timing_context": timing_context,
                "summary_logged": False,
            }
            self._playback_trace = trace
        self._log_playback_timing("player_play_started", trace)
        return trace

    def _log_playback_timing(
        self, stage: str, trace: Optional[Dict[str, Any]] = None
    ) -> None:
        current_trace = trace or self._playback_trace
        if not current_trace:
            return
        elapsed_ms = (
            time.perf_counter() - current_trace["started_at"]
        ) * 1000
        logging.info(
            "[PlaybackTiming] "
            f"trace={current_trace['id']} "
            f"stage={stage} "
            f"elapsed_ms={elapsed_ms:.2f} "
            f"service={current_trace['service']} "
            f"track={current_trace['track']!r}"
        )
        if stage == "playback-restart":
            self._log_playback_total(current_trace)

    def _log_playback_total(self, trace: Dict[str, Any]) -> None:
        context = trace["timing_context"]
        if not context or trace["summary_logged"]:
            return
        trace["summary_logged"] = True
        total_ms = (time.perf_counter() - context["started_at"]) * 1000
        kind = context["kind"]
        details = f"query={context['query']!r} " if kind == "search" else ""
        logging.info(
            f"[PlaybackTiming] {kind}_to_playback_completed "
            f"total_ms={total_ms:.2f} {details}"
            f"service={trace['service']} track={trace['track']!r}"
        )

    def _register_playback_timing_event(self, event_name: str) -> None:
        def callback(_: mpv.MpvEvent) -> None:
            self._log_playback_timing(event_name)
            if event_name in ("file-loaded", "playback-restart"):
                self._log_mpv_state(event_name)
            if event_name == "playback-restart":
                self.track._stream_refresh_attempted = False

        self.register_event_callback(event_name, callback)

    def _log_mpv_state(self, stage: str) -> None:
        trace = self._playback_trace
        if not trace:
            return
        cache_state = self._read_mpv_property("demuxer_cache_state") or {}
        logging.info(
            "[MPVState] "
            f"trace={trace['id']} stage={stage} "
            f"paused_for_cache={self._read_mpv_property('paused_for_cache')!r} "
            f"cache_buffering_state={self._read_mpv_property('cache_buffering_state')!r} "
            f"cache_duration={cache_state.get('cache-duration')!r} "
            f"forward_bytes={cache_state.get('fw-bytes')!r} "
            f"raw_input_rate={cache_state.get('raw-input-rate')!r} "
            f"underrun={cache_state.get('underrun')!r} "
            f"cache_idle={cache_state.get('idle')!r} "
            f"current_ao={self._read_mpv_property('current_ao')!r} "
            f"audio_params={self._read_mpv_property('audio_params')!r}"
        )

    def _read_mpv_property(self, name: str) -> Any:
        try:
            return getattr(self._player, name)
        except Exception:
            return None

    def _sync_index_list(self) -> None:
        if self.mode == Mode.Random:
            if not hasattr(self, "_index_list") or not self._index_list:
                self.shuffle(True, preserve_current=True)
            elif len(self._index_list) < len(self.track_list):
                existing = set(self._index_list)
                missing = [i for i in range(len(self.track_list)) if i not in existing]
                random.shuffle(missing)
                self._index_list.extend(missing)

    def _prefetch_next_track(self) -> None:
        if not self._prefetch_lock.acquire(blocking=False):
            logging.info("[PlaybackTiming] next_track_prefetch_skipped reason=already_running")
            return
        started_at = time.perf_counter()
        try:
            # Se há faixa na fila, ela será a próxima — prefetch dela
            next_from_queue = self.queue.peek_next()
            if next_from_queue is not None:
                if not next_from_queue._is_fetched:
                    logging.info(f"Prefetching next track from queue: {next_from_queue.name}")
                    _ = next_from_queue.url
                    elapsed_ms = (time.perf_counter() - started_at) * 1000
                    logging.info(
                        "[PlaybackTiming] next_track_prefetch_completed "
                        f"elapsed_ms={elapsed_ms:.2f} source=queue "
                        f"service={next_from_queue.service} "
                        f"track={next_from_queue.name!r}"
                    )
                return

            if not self.track_list:
                return

            next_index = -1
            if self.mode == Mode.Random:
                self._sync_index_list()
                try:
                    current_pos = self._index_list.index(self.track_index)
                    if current_pos + 1 < len(self._index_list):
                        next_index = self._index_list[current_pos + 1]
                    elif len(self._index_list) > 0:
                        next_index = self._index_list[0]
                except (ValueError, IndexError, AttributeError):
                    pass
            elif self.mode == Mode.RepeatTrack:
                next_index = self.track_index
            else:
                if self.track_index + 1 < len(self.track_list):
                    next_index = self.track_index + 1
                elif self.mode == Mode.RepeatTrackList and len(self.track_list) > 0:
                    next_index = 0

            if next_index != -1 and next_index < len(self.track_list):
                next_track = self.track_list[next_index]
                if not next_track._is_fetched:
                    logging.info(f"Prefetching next track: {next_track.name}")
                    _ = next_track.url
                    elapsed_ms = (time.perf_counter() - started_at) * 1000
                    logging.info(
                        "[PlaybackTiming] next_track_prefetch_completed "
                        f"elapsed_ms={elapsed_ms:.2f} source=track_list "
                        f"service={next_track.service} track={next_track.name!r}"
                    )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            logging.warning(
                "[PlaybackTiming] next_track_prefetch_failed "
                f"elapsed_ms={elapsed_ms:.2f} error={e!r}"
            )
        finally:
            self._prefetch_lock.release()

    def play_from_queue(self, started_at: Optional[float] = None) -> bool:
        started_at = started_at or time.perf_counter()
        next_track = self.queue.pop_next()
        if next_track is None:
            return False

        logging.info(f"Playing from queue: {next_track.name}")
        self.track_list = [next_track]
        self.track_index = 0
        self.track = next_track
        self._set_next_playback_context(started_at)
        self._play(next_track.url)
        self.state = State.Playing
        self._log_next_track_completed(started_at, "queue")
        return True

    def _get_track_video_id(self, track: Optional[Track]) -> Optional[str]:
        if not track:
            return None
        info = getattr(track, "extra_info", None) or {}
        vid = info.get("videoId") or info.get("id") or info.get("contentId")
        if vid:
            return str(vid)
        url = getattr(track, "_url", "")
        if url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0].split("?")[0]
            elif "youtu.be" in url:
                return url.split("/")[-1].split("?")[0]
        return None

    def _check_and_trigger_autoplay(self) -> None:
        try:
            if not self.track_list or self.mode == Mode.SingleTrack or self.is_playlist:
                return
            remaining = len(self.track_list) - 1 - self.track_index
            if remaining <= 4:
                candidates = []
                if self.track:
                    candidates.append(self.track)
                for t in reversed(self.track_list):
                    if t not in candidates:
                        candidates.append(t)

                for cand in candidates:
                    target_id = self._get_track_video_id(cand)
                    if target_id:
                        service_name = getattr(cand, "service", None) or self.bot.service_manager.service.name
                        service = self.bot.service_manager.get_service_by_name(service_name)
                        if hasattr(service, "_fetch_autoplay_async"):
                            service._fetch_autoplay_async(target_id)
                            break
        except Exception as e:
            logging.debug(f"[Player] Autoplay check trigger error: {e}")

    def _replenish_autoplay_sync(self) -> bool:
        try:
            if not self.track_list or self.mode == Mode.SingleTrack or self.is_playlist:
                return False
            candidates = []
            if self.track:
                candidates.append(self.track)
            for t in reversed(self.track_list):
                if t not in candidates:
                    candidates.append(t)

            for cand in candidates:
                target_id = self._get_track_video_id(cand)
                if target_id:
                    service_name = getattr(cand, "service", None) or self.bot.service_manager.service.name
                    service = self.bot.service_manager.get_service_by_name(service_name)
                    if hasattr(service, "_fetch_autoplay_sync"):
                        if service._fetch_autoplay_sync(target_id):
                            return True
        except Exception as e:
            logging.warning(f"[Player] Sync autoplay replenishment error: {e}")
        return False

    def next(self) -> None:
        with self._navigation_lock:
            self._next_locked()

    def _next_locked(self) -> None:
        started_at = time.perf_counter()
        previous_track = self.track.name or "Unknown"
        logging.info(
            "[PlaybackTiming] next_track_started "
            f"previous_track={previous_track!r} queue_size={self.queue.size}"
        )
        if not self.queue.is_empty:
            if self.play_from_queue(started_at):
                return

        track_index = self.track_index
        if len(self.track_list) > 0:
            if self.mode == Mode.Random:
                self._sync_index_list()
                try:
                    current_position = self._index_list.index(self.track_index)
                    if current_position + 1 < len(self._index_list):
                        track_index = self._index_list[current_position + 1]
                    else:
                        if self.is_playlist and self.mode != Mode.RepeatTrackList:
                            raise errors.NoNextTrackError()
                        self.shuffle(True)
                        track_index = self._index_list[0] if self._index_list else 0
                except (IndexError, ValueError, AttributeError):
                    if self.is_playlist and self.mode != Mode.RepeatTrackList:
                        raise errors.NoNextTrackError()
                    self.shuffle(True)
                    track_index = self._index_list[0] if self._index_list else 0
            else:
                track_index += 1
        else:
            track_index = 0

        if track_index >= len(self.track_list):
            if self.mode == Mode.RepeatTrackList:
                self._set_next_playback_context(started_at)
                self.play_by_index(0)
                self._log_next_track_completed(started_at, "repeat_track_list")
                return
            if not self.is_playlist:
                self._replenish_autoplay_sync()
            if track_index >= len(self.track_list):
                raise errors.NoNextTrackError()

        try:
            self._set_next_playback_context(started_at)
            self.play_by_index(track_index)
            self._log_next_track_completed(started_at, "track_list")
        except errors.IncorrectTrackIndexError:
            if self.mode == Mode.RepeatTrackList:
                self._set_next_playback_context(started_at)
                self.play_by_index(0)
                self._log_next_track_completed(started_at, "repeat_track_list")
            elif self.mode == Mode.Random and not self.is_playlist:
                self.shuffle(True)
                self._set_next_playback_context(started_at)
                self.play_by_index(self._index_list[0] if self._index_list else 0)
                self._log_next_track_completed(started_at, "random")
            else:
                raise errors.NoNextTrackError()

    def _set_next_playback_context(self, started_at: float) -> None:
        self._pending_playback_context = {
            "kind": "next_track",
            "started_at": started_at,
        }

    def _log_next_track_completed(self, started_at: float, source: str) -> None:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logging.info(
            "[PlaybackTiming] next_track_submitted "
            f"elapsed_ms={elapsed_ms:.2f} source={source} "
            f"service={self.track.service} track={self.track.name!r}"
        )

    def previous(self) -> None:
        track_index = self.track_index
        if len(self.track_list) > 0:
            if self.mode == Mode.Random:
                self._sync_index_list()
                try:
                    current_position = self._index_list.index(self.track_index)
                    if current_position > 0:
                        track_index = self._index_list[current_position - 1]
                    else:
                        track_index = self._index_list[-1]
                except (IndexError, ValueError, AttributeError):
                    track_index = self.track_index
            else:
                if track_index == 0 and self.mode != Mode.RepeatTrackList:
                    raise errors.NoPreviousTrackError
                else:
                    track_index -= 1
        else:
            track_index = 0
        try:
            self.play_by_index(track_index)
        except errors.IncorrectTrackIndexError:
            if self.mode == Mode.RepeatTrackList:
                self.play_by_index(len(self.track_list) - 1)
            else:
                raise errors.NoPreviousTrackError

    def play_by_index(self, index: int) -> None:
        if index < len(self.track_list) and index >= (0 - len(self.track_list)):
            self.track = self.track_list[index]
            self.track_index = index if index >= 0 else len(self.track_list) + index
            try:
                self._play(self.track.url)
                self.state = State.Playing
                self._check_and_trigger_autoplay()
            except errors.ServiceError as e:
                logging.warning(f"[Player] Track '{self.track.name}' is unplayable ({e}). Auto-skipping to next track...")
                if self.mode != Mode.SingleTrack and len(self.track_list) > index + 1:
                    self.next()
                else:
                    raise
        else:
            raise errors.IncorrectTrackIndexError()

    def set_volume(self, volume: int) -> None:
        volume = volume if volume <= self.config.max_volume else self.config.max_volume
        self.volume = volume
        if self.config.volume_fading:
            n = 1 if self._player.volume < volume else -1
            for i in range(int(self._player.volume), volume, n):
                self._player.volume = i
                time.sleep(self.config.volume_fading_interval)
        else:
            self._player.volume = volume

    def get_speed(self) -> float:
        return self._player.speed

    def set_speed(self, arg: float) -> None:
        if arg < 0.25 or arg > 4:
            raise ValueError()
        self._player.speed = arg

    def seek_back(self, step: Optional[float] = None) -> None:
        step = step if step else self.config.seek_step
        if step <= 0:
            raise ValueError()
        try:
            self._player.seek(-step, reference="relative")
        except SystemError:
            self.stop()

    def seek_forward(self, step: Optional[float] = None) -> None:
        step = step if step else self.config.seek_step
        if step <= 0:
            raise ValueError()
        try:
            self._player.seek(step, reference="relative")
        except SystemError:
            self.stop()

    def get_duration(self) -> float:
        return self._player.duration

    """def get_position(self) -> float:
        return self._player.time_pos

    def set_position(self, arg: float) -> None:
        if arg < 0:
            raise errors.IncorrectPositionError()
        self._player.seek(arg, reference="absolute")"""

    def get_output_devices(self) -> List[SoundDevice]:
        devices: List[SoundDevice] = []
        for device in self._player.audio_device_list:
            devices.append(
                SoundDevice(
                    device["description"], device["name"], SoundDeviceType.Output
                )
            )
        return devices

    def set_output_device(self, id: str) -> None:
        self._player.audio_device = id

    def shuffle(self, enable: bool, preserve_current: bool = False) -> None:
        if enable:
            if not self.track_list:
                self._index_list = []
                return
            indices = list(range(len(self.track_list)))
            if preserve_current and self.track_index in indices:
                indices.remove(self.track_index)
                random.shuffle(indices)
                self._index_list = [self.track_index] + indices
            else:
                random.shuffle(indices)
                self._index_list = indices
            logging.info(f"[Player] Shuffled playlist of {len(self.track_list)} tracks 100% randomly (preserve_current={preserve_current}). First picked track index: {self._index_list[0] if self._index_list else None}")
        else:
            if hasattr(self, "_index_list"):
                del self._index_list

    def register_event_callback(
        self, callback_name: str, callback_func: Callable[[mpv.MpvEvent], None]
    ) -> None:
        self._player.event_callback(callback_name)(callback_func)

    def log_handler(self, level: str, component: str, message: str) -> None:
        logging.log(self._log_level, "{}: {}: {}".format(level, component, message))

    def _parse_metadata(self, metadata: Dict[str, Any]) -> str:
        stream_names = ["icy-name"]
        stream_name = None
        title = None
        artist = None
        for i in metadata or {}:
            if not isinstance(metadata[i], str):
                continue
            if i in stream_names:
                stream_name = html.unescape(metadata[i])
            if "title" in i:
                title = html.unescape(metadata[i])
            if "artist" in i:
                artist = html.unescape(metadata[i])
        chunks: List[str] = []
        chunks.append(artist) if artist else ...
        chunks.append(title) if title else ...
        chunks.append(stream_name) if stream_name else ...
        return " - ".join(chunks)

    def on_end_file(self, event: Any) -> None:
        if isinstance(event, dict):
            payload = event
        elif hasattr(event, "as_dict"):
            payload = event.as_dict()
        else:
            payload = {"event": getattr(event, "event", {})}
        # Older bindings nest event data; current python-mpv returns a flat
        # mapping with byte-string event names and reasons.
        nested = payload.get("event")
        event_data = nested if isinstance(nested, dict) else payload
        reason = event_data.get("reason")
        if isinstance(reason, bytes):
            reason = reason.decode("utf-8", errors="replace")
        if isinstance(reason, str):
            reason = {
                "eof": mpv.MpvEventEndFile.EOF,
                "error": mpv.MpvEventEndFile.ERROR,
            }.get(reason)
        if reason not in (mpv.MpvEventEndFile.EOF, mpv.MpvEventEndFile.ERROR):
            logging.info(
                "[PlaybackTiming] end_file_ignored "
                f"reason={reason} track={self.track.name!r}"
            )
            return
        if (
            reason == mpv.MpvEventEndFile.ERROR
            and self.track.service in ("yt", "ytm")
            and not getattr(self.track, "_stream_refresh_attempted", False)
        ):
            self.track._stream_refresh_attempted = True
            try:
                logging.warning(
                    "[PlaybackTiming] youtube_stream_refresh_started "
                    f"track={self.track.name!r}"
                )
                refreshed_url = self.track.refresh_stream()
                self._play(refreshed_url, save_to_recents=False)
                return
            except Exception as error:
                logging.error(
                    "[PlaybackTiming] youtube_stream_refresh_failed "
                    f"track={self.track.name!r} error={error!r}"
                )
        if self.state == State.Playing and self._player.idle_active:
            if self.mode == Mode.SingleTrack or self.track.type == TrackType.Direct:
                # Mesmo em SingleTrack/Direct, a fila tem prioridade
                if not self.queue.is_empty:
                    self.play_from_queue()
                else:
                    self.stop()
            elif self.mode == Mode.RepeatTrack:
                # RepeatTrack repete a atual — fila NÃO interrompe automaticamente
                # O usuário pode usar 'qs' para pular para a fila manualmente
                self.play_by_index(self.track_index)
            else:
                # Para todos os outros modos, a fila tem prioridade
                if not self.queue.is_empty:
                    self.play_from_queue()
                else:
                    try:
                        self.next()
                    except errors.NoNextTrackError:
                        self.stop()

    def on_metadata_update(self, name: str, value: Any) -> None:
        if self.state == State.Playing and (
            self.track.type == TrackType.Direct or self.track.type == TrackType.Local
        ):
            metadata = self._player.metadata
            try:
                new_name = self._parse_metadata(metadata)
                if not new_name:
                    new_name = html.unescape(self._player.media_title or "")
            except TypeError:
                new_name = html.unescape(self._player.media_title or "")
            if self.track.name != new_name and new_name:
                self.track.name = new_name
