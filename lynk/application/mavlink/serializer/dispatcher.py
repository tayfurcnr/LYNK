from __future__ import annotations
from typing import Any, Dict, Optional
import time
from lynk.shared.log.logger import logger

_PB = None

def _get_pb():
    global _PB
    if _PB is not None:
        return _PB
        
    import sys
    import os
    # Adjusted path for lynk package structure
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    proto_dir = os.path.join(root_dir, "lynk/shared/proto")
    if proto_dir not in sys.path:
        sys.path.append(proto_dir)

    try:
        from lynk.shared.proto.msg.mavlink import mavlink_tunnel_pb2 as mavlink_pb
        _PB = mavlink_pb
        return _PB
    except Exception as exc:
        raise RuntimeError(
            "MAVLink protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc

def serialize_mavlink(
    payload: bytes,
    system_id: int = 1,
    component_id: int = 1,
    timestamp_us: Optional[int] = None
) -> bytes:
    """
    Serializes a raw MAVLink packet into a LYNK-compatible protobuf payload.
    """
    mavlink_pb = _get_pb()
    msg = mavlink_pb.MavlinkTunnel()
    msg.payload = payload
    msg.system_id = system_id
    msg.component_id = component_id
    msg.timestamp_us = timestamp_us if timestamp_us is not None else int(time.time() * 1e6)
    
    return msg.SerializeToString()

def deserialize_mavlink(data: bytes) -> dict:
    """
    Deserializes a LYNK-compatible protobuf payload back into a MAVLink structure.
    """
    mavlink_pb = _get_pb()
    msg = mavlink_pb.MavlinkTunnel()
    msg.ParseFromString(data)
    
    return {
        "payload": msg.payload,
        "system_id": msg.system_id,
        "component_id": msg.component_id,
        "timestamp_us": msg.timestamp_us
    }
