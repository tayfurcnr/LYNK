from __future__ import annotations
# /src/telemetry/tools/cache.py

"""
Telemetry Cache Module

Provides in-memory storage and retrieval of telemetry data for multiple devices,
indexed by source ID and data type. Each data entry is timestamped on insertion.
"""

import time
import threading
import random
from typing import Any, Dict, Optional

_lock = threading.Lock()
# Internal cache structure:
# {
#     src_id: {
#         "team_id": int | None,
#         "last_hop_count": int,
#         "telemetry": {
#             data_type: {
#                 ... arbitrary telemetry fields ...,
#                 "timestamp": float
#             },
#             ...
#         }
#     },
#     ...
# }
_device_cache: Dict[int, Dict[str, Any]] = {}


def _current_timestamp() -> float:
    """
    Return a monotonic time reference (not affected by system clock resets).
    """
    return time.monotonic()


def set_device_data(src_id: int, data_type: str, data: Dict[str, Any], team_id: Optional[int] = None, hop_count: int = 0) -> None:
    """
    Store or update telemetry data for a given device and data type.
    Adds a 'timestamp' field indicating the insertion time.

    Args:
        src_id (int): Unique identifier of the source device.
        data_type (str): Category of telemetry data (e.g., "gps", "imu").
        data (dict): Telemetry payload. Must be a dictionary.
        team_id (int, optional): Team identifier for the device.
        hop_count (int, optional): Number of hops the packet traveled.

    Raises:
        TypeError: If src_id is not int, data_type is not str, or data is not dict.
    """
    if not isinstance(src_id, int):
        raise TypeError(f"'src_id' must be int, got {type(src_id).__name__}")
    if not isinstance(data_type, str):
        raise TypeError(f"'data_type' must be str, got {type(data_type).__name__}")
    if not isinstance(data, dict):
        raise TypeError(f"'data' must be dict, got {type(data).__name__}")

    # Timestamp the data entry
    data["timestamp"] = _current_timestamp()

    with _lock:
        # Initialize device entry if absent
        if src_id not in _device_cache:
            _device_cache[src_id] = {
                "team_id": team_id,
                "last_hop_count": hop_count,
                "telemetry": {}
            }
        
        # Update team_id and hop_count if provided
        if team_id is not None:
            _device_cache[src_id]["team_id"] = team_id
        
        if hop_count is not None:
            _device_cache[src_id]["last_hop_count"] = hop_count

        _device_cache[src_id]["telemetry"][data_type] = data
        
        # Periodic Cleanup (Every 50 writes to keep it efficient)
        if len(_device_cache) > 0 and random.randint(1, 50) == 1:
            _cleanup_unlocked()


def get_device_data(src_id: int, data_type: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the latest telemetry data for a specific device and data type.

    Args:
        src_id (int): Device identifier.
        data_type (str): Telemetry category.

    Returns:
        dict or None: The telemetry payload including 'timestamp', or None if not found.
    """
    with _lock:
        return _device_cache.get(src_id, {}).get("telemetry", {}).get(data_type)


def get_active_device_ids(timeout: float = 5.0, team_id: Optional[int] = None) -> list[int]:
    """
    List device IDs that have sent any telemetry within the past `timeout` seconds.

    Args:
        timeout (float): Time window in seconds to consider a device active.
        team_id (int, optional): If provided, only include devices belonging to this team.

    Returns:
        List[int]: Sorted list of active device source IDs.
    """
    now = _current_timestamp()
    active_ids: list[int] = []

    with _lock:
        for src_id, device_info in _device_cache.items():
            # Team filter
            if team_id is not None and device_info.get("team_id") != team_id:
                continue

            # If any data entry is recent enough, mark device as active
            telemetry = device_info.get("telemetry", {})
            for entry in telemetry.values():
                if now - entry.get("timestamp", 0) <= timeout:
                    active_ids.append(src_id)
                    break

    return sorted(active_ids)


def get_all_data_for_device(src_id: int) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Retrieve all telemetry entries for a given device.

    Args:
        src_id (int): Device identifier.

    Returns:
        Dict[data_type, payload] or None: Mapping of data types to their latest payloads.
    """
    with _lock:
        return _device_cache.get(src_id, {}).get("telemetry")


def get_all_cached_data() -> Dict[int, Dict[str, Any]]:
    """
    Retrieve the entire telemetry cache.

    Returns:
        Dict[src_id, device_info]: Complete cache snapshot.
    """
    with _lock:
        import copy
        return copy.deepcopy(_device_cache)


def get_device_hop_count(src_id: int) -> int:
    """Retrieve the last known hop count for a device."""
    with _lock:
        return _device_cache.get(src_id, {}).get("last_hop_count", 0)

def _cleanup_unlocked(ttl_seconds: float = 3600):
    """Internal cleanup without acquiring lock (caller must hold it)."""
    now = _current_timestamp()
    to_delete = []
    for src_id, info in _device_cache.items():
        telemetry = info.get("telemetry", {})
        # If latest telemetry for this device is older than TTL, mark for removal
        if not telemetry:
            to_delete.append(src_id)
            continue
            
        latest = max(t.get("timestamp", 0) for t in telemetry.values())
        if now - latest > ttl_seconds:
            to_delete.append(src_id)
            
    for sid in to_delete:
        del _device_cache[sid]

def cleanup_stale_data(ttl_seconds: float = 3600):
    """Public cleanup method."""
    with _lock:
        _cleanup_unlocked(ttl_seconds)

def reset_cache() -> None:
    """
    Clear all stored telemetry data from the cache.
    """
    with _lock:
        _device_cache.clear()