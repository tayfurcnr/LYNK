from __future__ import annotations
import time
from lynk.application.event.serializer.dispatcher import deserialize_event
from lynk.application.event.definitions import event_definitions
from lynk.shared.log.logger import logger

# Duplicate detection cache
_received_events = {}  # (vehicle_id, boot_counter, sequence) -> timestamp_ms
CACHE_TTL_MS = 60000
_last_cleanup = 0
CLEANUP_INTERVAL_MS = 10000

def cleanup_expired_events():
    """Periyodik cache temizliği"""
    now_ms = time.time() * 1000
    expired = [k for k, v in _received_events.items() if now_ms - v > CACHE_TTL_MS]
    for k in expired:
        del _received_events[k]
    if expired:
        logger.debug(f"[EVENT] Cleaned {len(expired)} expired events")

def handle_event(payload: bytes, frame_meta: dict, interface=None):
    """
    Parse and handle an incoming 'E' (Event) frame.
    
    Args:
        payload (bytes): Raw event payload.
        frame_meta (dict): Frame metadata including src_id, dst_id, etc.
        interface: Optional interface object.
    """
    global _last_cleanup
    
    try:
        event_data = deserialize_event(payload)
        
        # Extract metadata
        source_vehicle_id = event_data.get("source_vehicle_id")
        boot_counter = event_data.get("boot_counter")
        sequence = event_data.get("sequence")
        event_type = event_data.get("event_type")
        priority = event_data.get("priority")
        timestamp_ms = event_data.get("timestamp_ms")
        
        # Periyodik cleanup
        now_ms = time.time() * 1000
        if now_ms - _last_cleanup > CLEANUP_INTERVAL_MS:
            cleanup_expired_events()
            _last_cleanup = now_ms
        
        # Duplicate check
        event_key = (source_vehicle_id, boot_counter, sequence)
        if event_key in _received_events:
            logger.debug(f"[EVENT] Duplicate ignored: {event_key}")
            return
        
        # İlk kez alıyoruz
        _received_events[event_key] = timestamp_ms
        
        # Get event definition
        event_def = event_definitions.get(event_type)
        if event_def:
            logger.info(f"[EVENT] RECV | TYPE: {event_def.name} | SRC: {source_vehicle_id} | PRIORITY: {priority}")
            
            try:
                event_def.handler(event_type, event_data, source_vehicle_id, interface)
                logger.debug(f"[EVENT] HANDLED | EVENT: {event_type} ({event_def.name})")
            except Exception as e:
                logger.error(f"[EVENT] HANDLER EXCEPTION | EVENT: {event_type}: {e}")
                raise e
        else:
            logger.warning(f"[EVENT] Unknown event type {event_type} from SRC: {source_vehicle_id}")
    
    except Exception as e:
        logger.error(f"[EVENT] ERROR | Failed to handle event: {e}")
        logger.debug(f"[EVENT] Exception detail:", exc_info=True)
