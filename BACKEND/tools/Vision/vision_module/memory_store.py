"""
Short-term memory for the vision tool.

This is deliberately narrow: it only tracks which images are "in play" for a
session so the user doesn't have to re-upload a screenshot every time they
ask a follow-up question. It is NOT the orchestrator's chat memory -- that's
a separate concern owned by the orchestrator.

NOTE on scaling: this in-memory dict is fine for a single-process hackathon
prototype. The moment you run multiple backend workers (uvicorn --workers N,
or multiple machines), sessions will land on different processes and this
store will look inconsistent. Swap the dict for Redis (same interface,
just backed by redis.hset / redis.expire) before that becomes a problem.
"""

import time
import threading
from typing import Dict, List, Optional

from .schemas import ImageRef


class ShortTermImageMemory:
    def __init__(self, ttl_seconds: int = 1800, max_images_per_session: int = 20):
        self._store: Dict[str, List[ImageRef]] = {}
        self._lock = threading.Lock()
        self.ttl_seconds = ttl_seconds
        self.max_images_per_session = max_images_per_session

    def add_image(self, session_id: str, image: ImageRef) -> None:
        with self._lock:
            images = self._store.setdefault(session_id, [])
            images.append(image)
            if len(images) > self.max_images_per_session:
                images.pop(0)  # drop oldest so memory doesn't grow unbounded

    def get_images(self, session_id: str, image_ids: Optional[List[str]] = None) -> List[ImageRef]:
        with self._lock:
            self._evict_expired(session_id)
            images = self._store.get(session_id, [])
            if image_ids:
                wanted = set(image_ids)
                return [img for img in images if img.image_id in wanted]
            return list(images)

    def clear_session(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def _evict_expired(self, session_id: str) -> None:
        now = time.time()
        images = self._store.get(session_id, [])
        fresh = [img for img in images if now - img.timestamp <= self.ttl_seconds]
        self._store[session_id] = fresh
