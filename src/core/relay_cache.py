import random
import time
import threading

class RelayCache:
    """
    Tracks recently seen packets to prevent duplicate relays.
    Uses (src_id, seq_num) as unique packet identifier.
    """
    
    def __init__(self, ttl_seconds: int = 30):
        self._cache = {}  # (src_id, seq_num) -> timestamp
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
    
    def is_duplicate(self, src_id: int, seq_num: int) -> bool:
        """Check if packet was already seen recently."""
        with self._lock:
            key = (src_id, seq_num)
            now = time.monotonic()
            
            # Efficient Cleanup: Only run cleanup 5% of the time or if cache is huge
            if len(self._cache) > 0 and (random.random() < 0.05 or len(self._cache) > 500):
                self._cache = {k: v for k, v in self._cache.items() if now - v < self._ttl}
            
            if key in self._cache:
                return True  # Duplicate
            
            # Mark as seen
            self._cache[key] = now
            return False

# Global instance
_instance = None

def get_relay_cache() -> RelayCache:
    global _instance
    if _instance is None:
        _instance = RelayCache()
    return _instance
