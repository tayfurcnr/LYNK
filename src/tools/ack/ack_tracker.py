# src/tools/ack/ack_tracker.py

import time
from typing import Dict, Tuple, Optional

# (cmd_name, dst_id) → {status, timestamp}
_ack_buffer: Dict[Tuple[str, int], Dict[str, float]] = {}

def _now() -> float:
    return time.time()

def register_ack(cmd_name: str, dst_id: int, status: int):
    """
    Gelen bir ACK mesajını buffer'a kaydeder.

    Args:
        cmd_name (str): Komut ismi (örneğin "TAKEOFF")
        dst_id (int): Komutun gönderildiği cihaz ID'si
        status (int): Komutun sonucu (örneğin 0 → SUCCESS)
    """
    _ack_buffer[(cmd_name.upper(), dst_id)] = {
        "status": status,
        "timestamp": _now()
    }

def get_ack_status(cmd_name: str, dst_id: int, timeout: float = 5.0) -> Optional[str]:
    """
    Belirtilen komutun son ACK durumunu döner.

    Returns:
        - "SUCCESS" (0)
        - "EXPIRED" (süre dolmuş)
        - None (henüz yok)
        - int (başka bir status)
    """
    key = (cmd_name.upper(), dst_id)
    entry = _ack_buffer.get(key)

    if entry is None:
        return None

    if _now() - entry["timestamp"] > timeout:
        return "EXPIRED"

    return entry["status"]

def clear_ack(cmd_name: str, dst_id: int):
    _ack_buffer.pop((cmd_name.upper(), dst_id), None)

def clear_all_acks():
    _ack_buffer.clear()

def get_all_acks() -> Dict[Tuple[str, int], Dict[str, float]]:
    return dict(_ack_buffer)
