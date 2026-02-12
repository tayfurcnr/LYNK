from __future__ import annotations
from typing import Optional
from lynk.core.frame_codec import build_mesh_frame
from lynk.shared.comm.interfaces import CommInterface
from lynk.application.mavlink.serializer.dispatcher import serialize_mavlink
from lynk.shared.log.logger import logger

# Internal callback storage
_mavlink_callbacks = []

def clear_mavlink_callbacks():
    """
    Clears all registered MAVLink callbacks.
    Use this before re-registering to prevent duplicate callbacks.
    """
    global _mavlink_callbacks
    _mavlink_callbacks.clear()

def on_mavlink_received(callback):
    """
    Registers a callback to be executed when a MAVLink packet is received.
    
    Callback signature: func(raw_payload: bytes, tunnel_meta: dict, frame_meta: dict)
    """
    if callback not in _mavlink_callbacks:
        _mavlink_callbacks.append(callback)
    return callback

def _trigger_mavlink_callbacks(raw_payload: bytes, tunnel_meta: dict, frame_meta: dict):
    """Internal use only: triggers all registered MAVLink callbacks."""
    for cb in _mavlink_callbacks:
        try:
            cb(raw_payload, tunnel_meta, frame_meta)
        except Exception as e:
            logger.error(f"[MAVLINK] Callback error: {e}")

def send_mavlink(
    interface: CommInterface,
    payload: bytes,
    dst: int = 255,
    src: Optional[int] = None,
    system_id: int = 1,
    component_id: int = 1,
    team_id: Optional[int] = None
):
    """
    Sends a MAVLink packet tunneled inside a LYNK mesh frame.
    
    Frame type 'M' is used for MAVLink tunneling.
    """
    from lynk.core.frame_codec import load_device_id
    
    final_src = src if src is not None else load_device_id()
    
    # 1. Serialize to protobuf
    proto_payload = serialize_mavlink(
        payload=payload,
        system_id=system_id,
        component_id=component_id
    )
    
    # 2. Build LYNK Mesh Frame (Type 'M')
    frame = build_mesh_frame(
        frame_type='M',
        src_id=final_src,
        dst_id=dst,
        payload=proto_payload,
        team_id=team_id
    )
    
    # 3. Transmit
    interface.send(frame)
