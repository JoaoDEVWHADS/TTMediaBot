from __future__ import annotations

import threading
from collections import deque
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bot.player.track import Track


class QueueManager:
    
    def __init__(self) -> None:
        self._queue: deque = deque()
        self._lock = threading.Lock()

    def add(self, track: Track) -> int:
        with self._lock:
            self._queue.append(track)
            return len(self._queue)

    def pop_next(self) -> Optional[Track]:
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def peek_next(self) -> Optional[Track]:
        with self._lock:
            return self._queue[0] if self._queue else None

    def remove(self, index: int) -> bool:
        with self._lock:
            items = list(self._queue)
            if 0 <= index < len(items):
                del items[index]
                self._queue = deque(items)
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._queue.clear()

    def list_tracks(self) -> List[Track]:
        with self._lock:
            return list(self._queue)

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0

    @property
    def size(self) -> int:
        return len(self._queue)