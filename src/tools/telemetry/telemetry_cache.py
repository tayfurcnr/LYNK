# src/tools/telemetry/telemetry_cache.py

import time
from typing import Any, Dict, Optional, List
from src.tools.log.logger import logger

# Internal cache: {device_id: {data_type: {data_dict + timestamp}}}
_device_cache: Dict[int, Dict[str, Dict[str, Any]]] = {}

def _current_timestamp() -> float:
    return time.time()

# 🔹 Set data for a specific device and type
def set_device_data(device_id: int, data_type: str, data: Dict[str, Any]):
    if device_id not in _device_cache:
        _device_cache[device_id] = {}

    data["timestamp"] = _current_timestamp()
    _device_cache[device_id][data_type] = data

    logger.debug(f"[TELEMETRY_CACHE] Updated | Device: {device_id}, Type: {data_type}, Data: {data}")

# 🔹 Get data for a specific device and type
def get_device_data(device_id: int, data_type: str) -> Optional[Dict[str, Any]]:
    return _device_cache.get(device_id, {}).get(data_type)

# 🔹 Get all data types for a specific device
def get_all_data_for_device(device_id: int) -> Optional[Dict[str, Dict[str, Any]]]:
    return _device_cache.get(device_id)

# 🔹 Get the full cache
def get_all_devices_data() -> Dict[int, Dict[str, Dict[str, Any]]]:
    return _device_cache.copy()

# 🔹 Get the latest device ID (based on any data type)
def get_latest_device_id() -> Optional[int]:
    latest = None
    latest_ts = -1
    for device_id, types in _device_cache.items():
        for data in types.values():
            if data.get("timestamp", 0) > latest_ts:
                latest = device_id
                latest_ts = data["timestamp"]
    return latest

# 🔹 Get active device IDs based on timeout
def get_active_device_ids(timeout: float = 5.0) -> List[int]:
    now = _current_timestamp()
    active_ids = []
    for device_id, types in _device_cache.items():
        for data in types.values():
            if now - data.get("timestamp", 0) <= timeout:
                active_ids.append(device_id)
                break
    return sorted(active_ids)

# 🔹 Clear the entire cache (useful for tests)
def reset_cache():
    _device_cache.clear()
    logger.info("[TELEMETRY_CACHE] Cache Has Been Cleared.")
