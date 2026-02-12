from __future__ import annotations
import threading
import time
from typing import Dict, Optional, Any
from lynk.shared.log.logger import logger

GREEN_BOLD = "\033[92m\033[1m"
RESET = "\033[0m"

class ACKTracker:
    def __init__(self):
        # {session_id: {src_id: ack_type}}
        self._sessions: Dict[str | int, Dict[int, str]] = {}
        # {session_id: [expected_src_ids]}
        self._expected_ids: Dict[str | int, list[int]] = {}
        # {session_id: callback_func}
        self._callbacks: Dict[str | int, Any] = {}
        # {session_id: threading.Event} - for blocking wait
        self._completion_events: Dict[str | int, threading.Event] = {}
        self._lock = threading.Lock()

    def register_session(self, session_id: str | int, expected_ids: list[int], callback: Optional[Any] = None, timeout: float = 2.0):
        """
        Register a command for ACK tracking from multiple sources.
        """
        with self._lock:
            self._sessions[session_id] = {}
            self._expected_ids[session_id] = expected_ids
            self._callbacks[session_id] = callback
            event = threading.Event()
            self._completion_events[session_id] = event
            
            logger.debug(f"[TRACKER] Registered session for ID: {session_id}, EXPECTING: {expected_ids}")

        # Spawn timeout/check thread
        threading.Thread(target=self._session_waiter, args=(session_id, timeout), daemon=True).start()

    def _session_waiter(self, session_id: str | int, timeout: float):
        """Background thread to wait for session completion or timeout."""
        event = self._completion_events.get(session_id)
        if not event:
            return

        finished = event.wait(timeout)
        
        with self._lock:
            results = self._sessions.pop(session_id, {})
            expected = self._expected_ids.pop(session_id, [])
            callback = self._callbacks.pop(session_id, None)
            self._completion_events.pop(session_id, None)

        cmd_part = ""
        try:
            from lynk.application.command.tools.dispatcher import get_tx_cmd_name
            cmd_name = get_tx_cmd_name(session_id)
            if cmd_name:
                cmd_part = f" FOR: {cmd_name}"
        except Exception:
            cmd_part = ""

        if not finished:
            color = "\033[95m\033[1m"
            reset = "\033[0m"
            logger.warning(
                f"{color}[TRACKER] SESSION TIMEOUT{cmd_part} | TX_ID: {session_id} | RECEIVED: {len(results)}/{len(expected)}{reset}"
            )
        else:
            logger.info(
                f"{GREEN_BOLD}[TRACKER] SESSION COMPLETED{cmd_part} | TX_ID: {session_id}{RESET}"
            )

        if callback:
            try:
                callback(results)
            except Exception as e:
                logger.error(f"[TRACKER] Callback error for session {session_id}: {e}")

    def notify_ack(self, session_id: str | int, src_id: int, ack_type: str):
        """Notify that an ACK has been received from a specific source."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id][src_id] = ack_type
                
                # Check if all expected ACKs received
                expected = self._expected_ids.get(session_id, [])
                if all(sid in self._sessions[session_id] for sid in expected):
                    event = self._completion_events.get(session_id)
                    if event:
                        event.set()
                
                logger.debug(f"[TRACKER] Logged ACK {ack_type} from {src_id} for Session ID: {session_id}")

    def wait_for_session(self, cmd_id: int, timeout: float = 2.0) -> Dict[int, str]:
        """
        Block until a session completes or times out and return results.
        Note: sessions are keyed by transaction_id; this method treats cmd_id as session_id.
        """
        with self._lock:
            event = self._completion_events.get(cmd_id)
        if not event:
            return {}

        event.wait(timeout)
        with self._lock:
            results = self._sessions.get(cmd_id, {})
            return dict(results)

    def reset(self):
        """Reset all tracking data. Use cautiously, primarily for tests."""
        with self._lock:
            self._sessions.clear()
            self._expected_ids.clear()
            self._callbacks.clear()
            self._completion_events.clear()
            logger.debug("[TRACKER] Resetted all sessions")

# Singleton instance
_tracker = ACKTracker()

def get_ack_tracker() -> ACKTracker:
    return _tracker
