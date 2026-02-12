from __future__ import annotations
from lynk.application.mavlink.serializer.dispatcher import deserialize_mavlink
from lynk.shared.log.logger import logger

def handle_mavlink(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'M' (MAVLink) type frames.
    Deserializes the tünnelled MAVLink packet and triggers callbacks.
    """
    try:
        src_id = frame_meta.get("src_id")
        hop_count = frame_meta.get("hop_count", 0)
        
        # 1. Deserialize the LYNK -> MAVLink tunnel packet
        data = deserialize_mavlink(payload)
        raw_mavlink = data.get("payload")
        system_id = data.get("system_id")
        component_id = data.get("component_id")

        logger.debug(
            f"[MAVLINK] RECV | SYS:{system_id} COMP:{component_id} | "
            f"LEN:{len(raw_mavlink)} bytes | FROM LNK:{src_id} (HOPS:{hop_count})"
        )

        # 2. Trigger registered callbacks
        from lynk.application.mavlink.tools.dispatcher import _trigger_mavlink_callbacks
        _trigger_mavlink_callbacks(raw_mavlink, data, frame_meta)

    except Exception as e:
        logger.error(f"[MAVLINK] Error handling MAVLink frame: {e}")
        logger.debug(f"[MAVLINK] Full error: {e}", exc_info=True)
