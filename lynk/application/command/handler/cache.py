from datetime import datetime, timedelta
import threading

class CommandIdempotencyCache:
    def __init__(self, ttl_seconds=10):
        # Key: (src_id, transaction_id) -> Value: timestamp
        self._cache = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = threading.Lock()

    def is_processed(self, src_id: int, transaction_id: str) -> bool:
        """
        Check if the command with the given transaction ID from the source 
        has already been processed within the TTL window.
        """
        if not transaction_id:
            return False

        key = (src_id, transaction_id)
        now = datetime.now()

        with self._lock:
            # Clean expired entries
            self._cleanup(now)

            if key in self._cache:
                return True
            
            # Mark as processed
            self._cache[key] = now
            return False

    def _cleanup(self, now):
        """Remove expired entries."""
        keys_to_remove = [k for k, v in self._cache.items() if now - v > self._ttl]
        for k in keys_to_remove:
            del self._cache[k]

# Global instance
_cmd_idempotency_cache = CommandIdempotencyCache()

def get_cmd_idempotency_cache():
    return _cmd_idempotency_cache
