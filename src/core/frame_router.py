from __future__ import annotations
import time
import random
# src/core/frame_router.py

from src.application.command.handler.dispatcher import handle_command
from src.application.telemetry.handler.dispatcher import handle_telemetry
from src.application.ack.handler.dispatcher import handle_ack

from src.core.frame_codec import load_device_id, load_team_id, build_mesh_frame
from src.shared.log.logger import logger
from src.shared.config.manager import get_config
from src.core.relay_cache import get_relay_cache

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
    
    # Relay Logic: 
    # 1. Broadcasts (0xFF) -> Always relay (subject to team)
    # 2. Unicast (!= local_id) -> Relay to help it reach destination
    local_id = load_device_id()
    dst_id = frame_dict["dst_id"]
    
    if dst_id == local_id:
        # addressed to me, no need to relay after processing
        return False
        
    if frame_dict["src_id"] == local_id:
        # I am the source, don't relay my own packets coming back
        return False
        
    if dst_id not in [0xFF, 255]:
        # Dedicated Unicast Relay (Mesh Support)
        logger.debug(f"[RELAY] Helping unicast packet for DST={dst_id} reach its destination")
    
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
    
    # Duplicate detection (Anti-Replay at Relay level)
    cache = get_relay_cache()
    src_id = frame_dict["src_id"]
    seq_num = frame_dict.get("seq_num", 0)
    
    # Check if we already relayed this specific sequence from this source
    if cache.is_duplicate(src_id, seq_num):
        logger.debug(f"[RELAY] Duplicate detected (SRC={src_id}, SEQ={seq_num}). Already relayed.")
        return False
    
    return True

def relay_frame(frame_dict: dict, interface):
    """
    Relays a frame by incrementing hop_count and re-transmitting.
    """
    cfg = get_config().get("relay", {})
    
    # QoS: Priority-based delay
    frame_type = chr(frame_dict["frame_type"]) if isinstance(frame_dict["frame_type"], int) else frame_dict["frame_type"]
    
    if frame_type in ['C', 'A']:
        # High Priority: 5-15ms delay
        delay_min, delay_max = 0.005, 0.015
    else:
        # Low Priority (Telemetry/etc): 50-150ms delay
        # This reduces congestion and gives way to critical commands/acks
        delay_min, delay_max = 0.050, 0.150
        
    time.sleep(random.uniform(delay_min, delay_max))
    
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
        hop_count=new_hop_count,
        seq_num=frame_dict.get("seq_num")
    )
    
    interface.send(relayed_frame)
    logger.debug(f"[RELAY] Relayed frame from SRC={frame_dict['src_id']} (hop={new_hop_count})")

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

        # Loopback Filtering (Ignore our own frames)
        # Default: Loopback is DISABLED (False) unless explicitly enabled in config
        cfg = get_config().get("udp", {})
        enable_loopback = cfg.get("enable_loopback", False)
        
        if not enable_loopback and frame_dict.get("src_id") == local_id:
             # logger.debug(f"[ROUTER] IGNORED | LOOPBACK DETECTED (src={local_id})") 
             return False

        # Team ID Filtering (Allow same team OR Global Team ID 0)
        if remote_team_id is not None and remote_team_id != 0 and remote_team_id != local_team_id:
             logger.debug(f"[ROUTER] IGNORED | WRONG TEAM FRAME (remote_team={remote_team_id}, local_team={local_team_id})")
             return False

        is_for_me = (dst_id == local_id or dst_id == 0xFF or dst_id == 0x00)
        
        handler = dispatch_table.get(frame_type)

        if is_for_me and handler:
            if frame_type == 'A':
                logger.debug(f"[ROUTER] ACK FRAME | SRC: {frame_dict['src_id']} -> DST: {frame_dict['dst_id']}")
            else:
                logger.debug(f"[ROUTER] RECEIVED | FRAME_TYPE='{frame_type}' | SRC: {frame_dict['src_id']} -> DST: {frame_dict['dst_id']}")
            handler(payload, frame_dict, interface)
            
        # Relay logic: check if we should relay (even if not for me)
        if should_relay_frame(frame_dict):
            relay_frame(frame_dict, interface)
        
        return True

    except Exception as e:
        logger.error(f"[ROUTER] ERROR | Exception while routing frame: {e}")
        return False
