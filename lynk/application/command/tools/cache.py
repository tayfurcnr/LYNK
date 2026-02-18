from __future__ import annotations
# lynk/application/command/tools/cache.py

"""
Command Cache Module

Provides in-memory storage for the last received command, including its ID,
raw parameters, parsed parameters, and a timestamp.
"""

import time
import threading
import hashlib
import json
from typing import Any, Dict, Optional

# Internal cache structure for the last command:
# {
#     "command_id": int,
#     "params": bytes,
#     "parsed_params": Dict[str, Any],
#     "transaction_id": str,
#     "timestamp": float
# }
_last_command: Dict[str, Any] = {}
_cache_lock = threading.Lock()


def _params_hash(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        raw = json.dumps(value, sort_keys=True, default=str).encode("utf-8", errors="ignore")
    return hashlib.blake2s(raw, digest_size=8).hexdigest()


def _current_timestamp() -> float:
    """
    Return a monotonic time reference.
    """
    return time.monotonic()


def set_last_command(
    command_id: int,
    params: Any,
    parsed_params: Dict[str, Any],
    transaction_id: str = "",
) -> None:
    """
    Store the details of the last received command.
    """
    with _cache_lock:
        _last_command.clear() # Ensure only one command is stored
        _last_command["command_id"] = command_id
        _last_command["params"] = params
        _last_command["parsed_params"] = parsed_params
        _last_command["transaction_id"] = str(transaction_id or "")
        _last_command["timestamp"] = _current_timestamp()
    # DEBUG
    # print(f"[DEBUG-CACHE] SET | ID={command_id} | DICT_ID={id(_last_command)}")


def get_last_command() -> Optional[Dict[str, Any]]:
    """
    Retrieve the details of the last received command.
    """
    # DEBUG
    # print(f"[DEBUG-CACHE] GET | DICT_ID={id(_last_command)} | HAS_VAL={len(_last_command)>0}")
    with _cache_lock:
        return dict(_last_command) if _last_command else None


def reset_command_cache() -> None:
    """
    Clear the stored last command from the cache.
    """
    with _cache_lock:
        _last_command.clear()


def attach_transaction_id_if_match(command_id: int, params: Any, transaction_id: str) -> bool:
    """
    Atomically attach transaction_id to cached command only if command_id+params still match.
    Prevents race-window mis-association under concurrent command handling.
    """
    with _cache_lock:
        if not _last_command:
            return False
        if int(_last_command.get("command_id", -1)) != int(command_id):
            return False
        if _params_hash(_last_command.get("params", b"")) != _params_hash(params):
            return False
        _last_command["transaction_id"] = str(transaction_id or "")
        return True


def ingest_frame(frame: Dict[str, Any]) -> None:
    """
    Ingest a command frame and store it as the last command.
    
    Args:
        frame (Dict[str, Any]): Frame containing command_id, params, etc.
    """
    if not isinstance(frame, dict):
        return
        
    command_id = frame.get("command_id")
    if command_id is None:
        return
        
    params = frame.get("params", b"")
        
    parsed_params = frame.get("parsed_params", {})
    if not isinstance(parsed_params, dict):
        parsed_params = {}
    transaction_id = frame.get("transaction_id", "")

    set_last_command(command_id, params, parsed_params, transaction_id=transaction_id)
