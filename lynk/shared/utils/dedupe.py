from __future__ import annotations

import time
from typing import Dict, Hashable


class DedupeCache:
    def __init__(self, ttl_sec: float = 2.0):
        self.ttl_sec = ttl_sec
        self._seen: Dict[Hashable, float] = {}

    def allow(self, key: Hashable) -> bool:
        now = time.monotonic()
        last = self._seen.get(key)
        if last is None or now - last > self.ttl_sec:
            self._seen[key] = now
            return True
        return False
