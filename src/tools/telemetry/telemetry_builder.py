# src/tools//telemetry/telemetry_builder.py

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.serializers.telemetry_serializer import serialize_telemetry

def build_tlm_frame(tlm_id: int, params: list, dst: int = 0xFF, src: int = None) -> bytes:
    src = src or load_device_id()
    payload = serialize_telemetry(tlm_id, *params)
    return build_mesh_frame('T', src, dst, payload)

def build_tlm_gps(lat: float, lon: float, alt: float, dst: int = 0xFF, src: int = None) -> bytes:
    return build_tlm_frame(0x01, [lat, lon, alt], dst, src)

def build_tlm_imu(roll: float, pitch: float, yaw: float, dst: int = 0xFF, src: int = None) -> bytes:
    return build_tlm_frame(0x02, [roll, pitch, yaw], dst, src)

def build_tlm_battery(voltage: float, current: float, level: float, dst: int = 0xFF, src: int = None) -> bytes:
    return build_tlm_frame(0x03, [voltage, current, level], dst, src)
