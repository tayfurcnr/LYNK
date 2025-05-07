import time
from typing import Any, Dict, Optional

_device_cache: Dict[int, Dict[str, Dict[str, Any]]] = {}

def _current_timestamp() -> float:
    return time.time()

def set_device_data(src_id: int, data_type: str, data: Dict[str, Any]):
    if not isinstance(src_id, int):
        raise TypeError(f"'src_id' must be int, got {type(src_id).__name__}")
    if not isinstance(data_type, str):
        raise TypeError(f"'data_type' must be str, got {type(data_type).__name__}")
    if not isinstance(data, dict):
        raise TypeError(f"'data' must be dict, got {type(data).__name__}")

    data["timestamp"] = _current_timestamp()
    data["src_id"] = src_id

    if src_id not in _device_cache:
        _device_cache[src_id] = {}

    _device_cache[src_id][data_type] = data

def get_device_data(src_id: int, data_type: str) -> Optional[Dict[str, Any]]:
    return _device_cache.get(src_id, {}).get(data_type)

def get_active_device_ids(timeout: float = 5.0) -> list[int]:
    """
    Son `timeout` saniye içinde veri gönderen aktif cihazların src_id listesini döner.
    """
    now = _current_timestamp()
    active_ids = []
    for src_id, types in _device_cache.items():
        for data in types.values():
            if now - data.get("timestamp", 0) <= timeout:
                active_ids.append(src_id)
                break
    return sorted(active_ids)

def get_all_data_for_device(src_id: int) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Belirli bir cihazın (src_id) tuttuğu tüm telemetry data_type'larını döner.
    """
    return _device_cache.get(src_id)

def get_all_cached_data() -> Dict[int, Dict[str, Dict[str, Any]]]:
    """
    Cache'teki tüm cihazların tüm telemetry verilerini döner.
    """
    return _device_cache

def reset_cache():
    _device_cache.clear()
