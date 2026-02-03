from __future__ import annotations
# src/core/frame_router.py

from src.application.command.handler.dispatcher import handle_command
from src.application.telemetry.handler.dispatcher import handle_telemetry
from src.application.ack.handler.dispatcher import handle_ack

from src.core.frame_codec import load_device_id, load_team_id, build_mesh_frame
from src.shared.log.logger import logger
from src.shared.config.manager import get_config

# Frame Type → Handler Mapping
dispatch_table = {
    'C': handle_command,
    'T': handle_telemetry,
    'A': handle_ack,
}

def should_relay_frame(frame_dict: dict) -> bool:
    """
    Determines if a frame should be relayed to other nodes.
    Only broadcasts are relayed, with team filtering and TTL limits.
    """
    cfg = get_config().get("relay", {})
    
    # Check if relay is enabled
    if not cfg.get("enabled", False):
        return False
    
    # Only relay broadcast packets
    if frame_dict["dst_id"] not in [0xFF, 255]:
        return False
    
    # Team filtering: relay own team + global (team_id=0)
    my_team = load_team_id()
    pkt_team = frame_dict["team_id"]
    if pkt_team != 0 and pkt_team != my_team:
        return False
    
    # TTL check
    hop_count = frame_dict.get("hop_count", 0)
    max_hops = cfg.get("max_hops", 5)
    if hop_count >= max_hops:
        logger.debug(f"[RELAY] TTL exceeded: hop_count={hop_count} >= max_hops={max_hops}")
        return False
    
    # Duplicate detection
    from src.core.relay_cache import get_relay_cache
    from src.core.sequence_manager import get_sequence_manager
    
    # Extract sequence from payload (first 4 bytes after decryption)
    # Note: This is a simplified check, actual seq is inside encrypted payload
    # We use (src_id, hop_count) as a proxy for now
    cache = get_relay_cache()
    src_id = frame_dict["src_id"]
    
    # Use a simple heuristic: (src_id, payload_hash)
    payload_hash = hash(frame_dict["payload"][:16] if len(frame_dict["payload"]) >= 16 else frame_dict["payload"])
    
    if cache.is_duplicate(src_id, payload_hash):
        logger.debug(f"[RELAY] Duplicate detected from SRC={src_id}")
        return False
    
    return True

def relay_frame(frame_dict: dict, interface):
    """
    Relays a frame by incrementing hop_count and re-transmitting.
    """
    import time
    import random
    
    cfg = get_config().get("relay", {})
    delay_ms = cfg.get("delay_ms", 20)
    
    # Small random delay to avoid collisions
    time.sleep(random.uniform(delay_ms / 2000, delay_ms / 1000))
    
    # Rebuild frame with incremented hop_count
    new_hop_count = frame_dict["hop_count"] + 1
    
    # Get the original encrypted payload (before decryption in parse)
    # We need to rebuild from the parsed dict
    frame_type = chr(frame_dict["frame_type"]) if isinstance(frame_dict["frame_type"], int) else frame_dict["frame_type"]
    
    relayed_frame = build_mesh_frame(
        frame_type=frame_type,
        src_id=frame_dict["src_id"],
        dst_id=frame_dict["dst_id"],
        payload=frame_dict["payload"],
        team_id=frame_dict["team_id"],
        hop_count=new_hop_count
    )
    
    interface.send(relayed_frame)
    logger.info(f"[RELAY] Relayed frame from SRC={frame_dict['src_id']} (hop={new_hop_count})")

def route_frame(frame_dict: dict, interface) -> bool:
    """
    Routes a decoded mesh frame to the appropriate handler.
    Returns:
        bool: True if frame was accepted and dispatched, False otherwise.
    """

    try:
        frame_type = frame_dict.get("frame_type")
        dst_id = frame_dict.get("dst_id")
        payload = frame_dict.get("payload")

        # Convert frame_type to character if it's an integer
        if isinstance(frame_type, int):
            frame_type = chr(frame_type)

        local_id = load_device_id()
        local_team_id = load_team_id()
        remote_team_id = frame_dict.get("team_id")

        # Team ID Filtering (Allow same team OR Global Team ID 0)
        if remote_team_id is not None and remote_team_id != 0 and remote_team_id != local_team_id:
             logger.debug(f"[ROUTER] IGNORED | WRONG TEAM FRAME (remote_team={remote_team_id}, local_team={local_team_id})")
             return False

        if dst_id != 0xFF and dst_id != 0x00 and dst_id != local_id:
            logger.debug(f"[ROUTER] IGNORED | Frame not addressed to this node (dst_id={dst_id}, local_id={local_id})")
            return False

        handler = dispatch_table.get(frame_type)

        if handler:
            logger.debug(f"[ROUTER] RECEIVED | FRAME_TYPE='{frame_type}' | SRC: {frame_dict['src_id']} -> DST: {frame_dict['dst_id']}")
            handler(payload, frame_dict, interface)
            
            # Relay logic: after processing, check if we should relay
            if should_relay_frame(frame_dict):
                relay_frame(frame_dict, interface)
            
            return True
        else:
            logger.warning(f"[ROUTER] UNKNOWN FRAME_TYPE | '{frame_type}' from SRC: {frame_dict['src_id']}")
            return False

    except Exception as e:
        logger.error(f"[ROUTER] ERROR | Exception while routing frame: {e}")
        return False
