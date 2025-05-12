# src/tools/ack/ack_tracker.py

"""
ACK Tracker Module

Maintains a registry of acknowledgment statuses for issued commands,
allowing retrieval, expiration checks, and buffer management.
"""

import time
from typing import Dict, Tuple, Optional, Union

# Internal buffer:
# Key: (command_name_uppercase, destination_id)
# Value: {"status": int, "timestamp": float}
_ack_buffer: Dict[Tuple[str, int], Dict[str, float]] = {}


def _current_time() -> float:
    """
    Return the current time as a UNIX timestamp.
    """
    return time.time()


def register_ack(cmd_name: str, dst_id: int, status: int) -> None:
    """
    Record an ACK/NACK for a specific command and destination.

    Args:
        cmd_name (str): Command name (e.g., "TAKEOFF").
        dst_id (int): Destination device ID that sent the ACK.
        status (int): Status code (e.g., 0 for SUCCESS).
    """
    key = (cmd_name.upper(), dst_id)
    _ack_buffer[key] = {
        "status": status,
        "timestamp": _current_time()
    }


def get_ack_status(
    cmd_name: str,
    dst_id: int,
    timeout: float = 5.0
) -> Optional[Union[int, str]]:
    """
    Retrieve the most recent ACK status for a given command and destination.

    Args:
        cmd_name (str): Command name to query.
        dst_id (int): Destination device ID.
        timeout (float): Time window in seconds before an entry expires.

    Returns:
        int: The recorded status code if within timeout.
        "EXPIRED": If the recorded entry is older than `timeout`.
        None: If no ACK has been recorded.
    """
    key = (cmd_name.upper(), dst_id)
    entry = _ack_buffer.get(key)

    if entry is None:
        return None

    elapsed = _current_time() - entry["timestamp"]
    if elapsed > timeout:
        return "EXPIRED"

    return entry["status"]


def clear_ack(cmd_name: str, dst_id: int) -> None:
    """
    Remove the ACK entry for a given command and destination, if present.

    Args:
        cmd_name (str): Command name.
        dst_id (int): Destination device ID.
    """
    _ack_buffer.pop((cmd_name.upper(), dst_id), None)


def clear_all_acks() -> None:
    """
    Clear all recorded ACK entries.
    """
    _ack_buffer.clear()


def get_all_acks() -> Dict[Tuple[str, int], Dict[str, float]]:
    """
    Return a snapshot of all recorded ACK entries.

    Returns:
        Dict[(str, int), {"status": int, "timestamp": float}]:
            Copy of the internal ACK buffer.
    """
    return dict(_ack_buffer)
