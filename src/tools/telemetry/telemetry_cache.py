# /src/tools/telemetry/telemetry_cache.py

"""
Telemetry Cache Module

Provides in-memory storage and retrieval of telemetry data for multiple devices,
indexed by source ID and data type. Each data entry is timestamped on insertion.
"""

import time
from typing import Any, Dict, Optional

# Internal cache structure:
# {
#     src_id: {
#         data_type: {
#             ... arbitrary telemetry fields ...,
#             "timestamp": float
#         },
#         ...
#     },
#     ...
# }
_device_cache: Dict[int, Dict[str, Dict[str, Any]]] = {}


def _current_timestamp() -> float:
    """
    Return the current time as a UNIX timestamp (seconds since epoch).
    """
    return time.time()


def set_device_data(src_id: int, data_type: str, data: Dict[str, Any]) -> None:
    """
    Store or update telemetry data for a given device and data type.
    Adds a 'timestamp' field indicating the insertion time.

    Args:
        src_id (int): Unique identifier of the source device.
        data_type (str): Category of telemetry data (e.g., "gps", "imu").
        data (dict): Telemetry payload. Must be a dictionary.

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

    # Initialize device entry if absent
    if src_id not in _device_cache:
        _device_cache[src_id] = {}

    _device_cache[src_id][data_type] = data


def get_device_data(src_id: int, data_type: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the latest telemetry data for a specific device and data type.

    Args:
        src_id (int): Device identifier.
        data_type (str): Telemetry category.

    Returns:
        dict or None: The telemetry payload including 'timestamp', or None if not found.
    """
    return _device_cache.get(src_id, {}).get(data_type)


def get_active_device_ids(timeout: float = 5.0) -> list[int]:
    """
    List device IDs that have sent any telemetry within the past `timeout` seconds.

    Args:
        timeout (float): Time window in seconds to consider a device active.

    Returns:
        List[int]: Sorted list of active device source IDs.
    """
    now = _current_timestamp()
    active_ids: list[int] = []

    for src_id, entries in _device_cache.items():
        # If any data entry is recent enough, mark device as active
        for entry in entries.values():
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
    return _device_cache.get(src_id)


def get_all_cached_data() -> Dict[int, Dict[str, Dict[str, Any]]]:
    """
    Retrieve the entire telemetry cache, omitting any 'src_id' fields within entries.

    Returns:
        Dict[src_id, Dict[data_type, payload]]: Complete cache snapshot.
    """
    cleaned: Dict[int, Dict[str, Dict[str, Any]]] = {}

    for src_id, entries in _device_cache.items():
        cleaned[src_id] = {}
        for dtype, payload in entries.items():
            # Exclude any embedded 'src_id' keys from payload
            filtered = {k: v for k, v in payload.items() if k != "src_id"}
            cleaned[src_id][dtype] = filtered

    return cleaned


def reset_cache() -> None:
    """
    Clear all stored telemetry data from the cache.
    """
    _device_cache.clear()
