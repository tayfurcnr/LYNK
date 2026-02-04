from __future__ import annotations
# src/application/command/tools/cache.py

"""
Command Cache Module

Provides in-memory storage for the last received command, including its ID,
raw parameters, parsed parameters, and a timestamp.
"""

import time
from typing import Any, Dict, Optional

# Internal cache structure for the last command:
# {
#     "command_id": int,
#     "params": bytes,
#     "parsed_params": Dict[str, Any],
#     "timestamp": float
# }
_last_command: Dict[str, Any] = {}


def _current_timestamp() -> float:
    """
    Return the current time as a UNIX timestamp (seconds since epoch).
    """
    return time.time()


def set_last_command(command_id: int, params: Any, parsed_params: Dict[str, Any]) -> None:
    """
    Store the details of the last received command.
    """
    _last_command.clear() # Ensure only one command is stored
    _last_command["command_id"] = command_id
    _last_command["params"] = params
    _last_command["parsed_params"] = parsed_params
    _last_command["timestamp"] = _current_timestamp()
    # DEBUG
    # print(f"[DEBUG-CACHE] SET | ID={command_id} | DICT_ID={id(_last_command)}")


def get_last_command() -> Optional[Dict[str, Any]]:
    """
    Retrieve the details of the last received command.
    """
    # DEBUG
    # print(f"[DEBUG-CACHE] GET | DICT_ID={id(_last_command)} | HAS_VAL={len(_last_command)>0}")
    return _last_command if _last_command else None


def reset_command_cache() -> None:
    """
    Clear the stored last command from the cache.
    """
    _last_command.clear()


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
        
    set_last_command(command_id, params, parsed_params)
