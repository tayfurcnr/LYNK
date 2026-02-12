from __future__ import annotations
import threading
import time

class SequenceManager:
    """
    Manages sequence numbers for outgoing and incoming mesh frames.
    Prevents replay attacks by ensuring each packet has a unique, incrementing ID.
    """
    def __init__(self, reset_timeout_sec: float = 5.0):
        self._out_seq = 0
        self._in_seq_map = {} # lynk_id -> last_received_seq
        self._last_seen_map = {} # lynk_id -> monotonic timestamp
        self._reset_timeout_sec = reset_timeout_sec
        self._lock = threading.Lock()

    def get_next_out_seq(self) -> int:
        """Increments and returns the next outgoing sequence number."""
        with self._lock:
            self._out_seq = (self._out_seq + 1) & 0xFFFFFFFF # 32-bit wrap around
            return self._out_seq

    def verify_in_seq(self, src_id: int, seq_num: int) -> bool:
        """
        Verifies if the incoming sequence number is valid (greater than last seen).
        Updates the registry if valid.
        """
        with self._lock:
            now = time.monotonic()
            if src_id not in self._in_seq_map:
                # First time seeing this device
                self._in_seq_map[src_id] = seq_num
                self._last_seen_map[src_id] = now
                return True

            last_seq = self._in_seq_map[src_id]
            diff = (seq_num - last_seq) & 0xFFFFFFFF
            
            # Standard RFC 1982 / Mesh sequence comparison:
            # If 0 < (seq_num - last_seq) < 2^31, then seq_num is "greater" (newer)
            if 0 < diff < 0x80000000:
                self._in_seq_map[src_id] = seq_num
                self._last_seen_map[src_id] = now
                return True
            
            # Special case: allow explicitly resetting to 0 if we aren't already at 0
            if seq_num == 0 and last_seq != 0:
                self._in_seq_map[src_id] = seq_num
                self._last_seen_map[src_id] = now
                return True

            # Reset window: if we haven't seen this src for a while, accept lower seqs
            last_seen = self._last_seen_map.get(src_id, now)
            if now - last_seen >= self._reset_timeout_sec:
                self._in_seq_map[src_id] = seq_num
                self._last_seen_map[src_id] = now
                return True
            
            return False

# Global instance for the process
_instance = None

def get_sequence_manager() -> SequenceManager:
    global _instance
    if _instance is None:
        _instance = SequenceManager()
    return _instance
