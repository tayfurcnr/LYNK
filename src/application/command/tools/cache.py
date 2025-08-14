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


def set_last_command(command_id: int, params: bytes, parsed_params: Dict[str, Any]) -> None:
    """
    Store the details of the last received command.

    Args:
        command_id (int): The ID of the command.
        params (bytes): The raw parameters of the command.
        parsed_params (Dict[str, Any]): A dictionary of parsed parameters.
    """
    _last_command.clear() # Ensure only one command is stored
    _last_command["command_id"] = command_id
    _last_command["params"] = params
    _last_command["parsed_params"] = parsed_params
    _last_command["timestamp"] = _current_timestamp()


def get_last_command() -> Optional[Dict[str, Any]]:
    """
    Retrieve the details of the last received command.

    Returns:
        dict or None: A dictionary containing command_id, params, parsed_params,
                      and timestamp, or None if no command has been set.
    """
    return _last_command if _last_command else None


def reset_command_cache() -> None:
    """
    Clear the stored last command from the cache.
    """
    _last_command.clear()
