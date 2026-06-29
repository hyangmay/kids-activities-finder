"""A tiny in-memory TTL cache.

By design the app persists *nothing* to disk (see CLAUDE.md privacy notes). This cache
lives only in the process: it spares us from re-geocoding the same area or re-hitting a
source within a short window, and everything is discarded when the process exits.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Generic, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """Thread-safe key/value cache where entries expire after ``ttl_seconds``.

    Streamlit runs callbacks across threads, so access is guarded by a lock.
    """

    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[K, tuple[float, V]] = {}
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            self._store[key] = (time.monotonic() + self.ttl_seconds, value)

    def get_or_compute(self, key: K, compute: Callable[[], V]) -> V:
        """Return the cached value, or compute, store, and return it.

        ``compute`` runs outside the lock so a slow network call doesn't block other
        keys; a redundant concurrent miss is harmless here.
        """
        cached = self.get(key)
        if cached is not None:
            return cached
        value = compute()
        self.set(key, value)
        return value

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
