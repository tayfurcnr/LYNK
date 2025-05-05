# src/tools/command_builder.py

import struct
from src.frame_codec import build_mesh_frame, load_device_id
from src.serializers.command_serializer import serialize_command

def build_cmd_frame(cmd_id: int, params: bytes = b'', dst: int = 0xFF, src: int = None) -> bytes:
    src = src or load_device_id()
    payload = serialize_command(cmd_id, params)
    frame = build_mesh_frame('C', src, dst, payload)
    return frame

def build_cmd_reboot(dst: int, src: int = None) -> bytes:
    return build_cmd_frame(0x01, dst=dst, src=src)

def build_cmd_set_mode(mode: int, dst: int, src: int = None) -> bytes:
    params = bytes([mode])
    return build_cmd_frame(0x02, params, dst, src)

def build_cmd_takeoff(takeoff_alt: float,
                      target_lat: float = None, target_lon: float = None, target_alt: float = None,
                      dst: int = 0xFF, src: int = None) -> bytes:
    if target_lat is not None and target_lon is not None and target_alt is not None:
        params = struct.pack(">ffff", takeoff_alt, target_lat, target_lon, target_alt)
    else:
        params = struct.pack(">f", takeoff_alt)
    return build_cmd_frame(0x03, params, dst, src)

def build_cmd_landing(target_lat: float = None, target_lon: float = None,
                      dst: int = 0xFF, src: int = None) -> bytes:
    params = struct.pack(">ff", target_lat, target_lon) if target_lat and target_lon else b""
    return build_cmd_frame(0x04, params, dst, src)

def build_cmd_gimbal(yaw: float, pitch: float, roll: float,
                     dst: int = 0xFF, src: int = None) -> bytes:
    params = struct.pack(">fff", yaw, pitch, roll)
    return build_cmd_frame(0x05, params, dst, src)

def build_cmd_goto(target_lat: float, target_lon: float, target_alt: float,
                   dst: int = 0xFF, src: int = None) -> bytes:
    params = struct.pack(">fff", target_lat, target_lon, target_alt)
    return build_cmd_frame(0x06, params, dst, src)

def build_cmd_simple_follow_me(target_id: int, altitude: float = None,
                               dst: int = 0xFF, src: int = None) -> bytes:
    params = struct.pack(">If", target_id, altitude) if altitude is not None else struct.pack(">I", target_id)
    return build_cmd_frame(0x07, params, dst, src)

def build_cmd_waypoints(waypoints: list, dst: int = 0xFF, src: int = None) -> bytes:
    params = b''.join(struct.pack(">fff", lat, lon, alt) for lat, lon, alt in waypoints)
    return build_cmd_frame(0x09, params, dst, src)
