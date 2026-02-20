from __future__ import annotations
import time
from typing import Optional, Dict, Any
from lynk.application.event.serializer.dispatcher import get_event_payload_schema as _get_event_payload_schema
from lynk.application.event.serializer.dispatcher import serialize_event
from lynk.core.frame_codec import build_mesh_frame, load_device_id
from lynk.shared.log.logger import logger
from lynk.shared.config.manager import get_config

# Boot counter and sequence management
_boot_counter = 0
_event_sequence = 0
_rate_limiters = {}  # priority -> (tokens, last_refill_time)
_event_handlers: Dict[int, list] = {} # event_type -> list of callbacks

RATE_LIMITS = {3: 10, 2: 5, 1: 2, 0: 1}  # CRITICAL: 10, HIGH: 5, NORMAL: 2, LOW: 1


def get_event_payload_schema():
    """Public accessor exposed via lynk.event namespace."""
    return _get_event_payload_schema()

def register_handler(event_type: int, callback: Any) -> None:
    """
    Register a dynamic callback for a specific event type.
    
    Args:
        event_type (int): Event ID (e.g., 31 for BATTERY_LOW)
        callback (callable): Function taking event_data (dict)
    """
    if event_type not in _event_handlers:
        _event_handlers[event_type] = []
    _event_handlers[event_type].append(callback)
    logger.debug(f"[EVENT] Callback registered for TYPE: {event_type}")

def _get_dynamic_handlers(event_type: int) -> list:
    """Internal helper to fetch registered handlers."""
    return _event_handlers.get(event_type, [])

def load_boot_counter() -> int:
    """Load persistent boot counter from storage."""
    global _boot_counter
    # TODO: Implement persistent storage (EEPROM/flash)
    # For now, use in-memory counter
    return _boot_counter

def increment_boot_counter():
    """Increment boot counter on system boot."""
    global _boot_counter
    _boot_counter += 1
    # TODO: Save to persistent storage

def get_next_sequence() -> int:
    """Get next event sequence number."""
    global _event_sequence
    _event_sequence += 1
    return _event_sequence

def check_rate_limit(priority: int) -> bool:
    """Token bucket rate limiting."""
    now = time.time()
    max_rate = RATE_LIMITS.get(priority, 1)
    
    if priority not in _rate_limiters:
        _rate_limiters[priority] = [max_rate, now]
        return True
    
    tokens, last_refill = _rate_limiters[priority]
    
    # Refill tokens
    elapsed = now - last_refill
    tokens = min(max_rate, tokens + elapsed * max_rate)
    
    # Check if we have tokens
    if tokens >= 1.0:
        _rate_limiters[priority] = [tokens - 1.0, now]
        return True
    else:
        _rate_limiters[priority] = [tokens, now]
        logger.warning(f"[EVENT] Rate limit exceeded for priority {priority}")
        return False

def send_event(
    interface,
    event_type: int,
    priority: int,
    payload_params: Optional[Dict[str, Any]] = None,
    dst_id: int = 0xFF
):
    """
    Send an event with priority-based redundancy.
    
    Parameters:
        interface: Network interface
        event_type (int): Event type ID
        priority (int): Event priority (0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL)
        payload_params (dict): Event-specific parameters
        dst_id (int): Destination ID (default: 0xFF broadcast)
    """
    # Rate limiting check
    if not check_rate_limit(priority):
        return
    
    source_vehicle_id = load_device_id()
    _ = load_boot_counter()
    _ = get_next_sequence()
    
    # Serialize event
    event_payload = serialize_event(
        event_type=event_type,
        priority=priority,
        payload_params=payload_params,
    )
    
    # Build mesh frame
    frame = build_mesh_frame(
        frame_type='E',
        src_id=source_vehicle_id,
        dst_id=dst_id,
        payload=event_payload
    )
    
    # Get redundancy config
    cfg = get_config().get("event", {}).get("redundancy", {})
    
    # Priority-based redundancy
    if priority == 3:  # CRITICAL
        delays = cfg.get("critical", {}).get("delays_ms", [0, 50, 150])
    elif priority == 2:  # HIGH
        delays = cfg.get("high", {}).get("delays_ms", [0, 100])
    else:  # NORMAL/LOW
        delays = [0]
    
    # Send with delays
    for i, delay_ms in enumerate(delays):
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        interface.send(frame)
        if i == 0:
            logger.info(f"[EVENT] SENT | TYPE: {event_type} | PRIORITY: {priority} | DST: {dst_id:#04x}")
        else:
            logger.debug(f"[EVENT] REDUNDANT SEND #{i+1} | TYPE: {event_type}")
