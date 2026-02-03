from __future__ import annotations
import threading

class SequenceManager:
    """
    Manages sequence numbers for outgoing and incoming mesh frames.
    Prevents replay attacks by ensuring each packet has a unique, incrementing ID.
    """
    def __init__(self):
        self._out_seq = 0
        self._in_seq_map = {} # src_id -> last_received_seq
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
            last_seq = self._in_seq_map.get(src_id, 0)
            
            # Allow 0 for initial sync or if manager was reset
            if seq_num > last_seq or seq_num == 0:
                self._in_seq_map[src_id] = seq_num
                return True
            
            return False

# Global instance for the process
_instance = None

def get_sequence_manager() -> SequenceManager:
    global _instance
    if _instance is None:
        _instance = SequenceManager()
    return _instance
