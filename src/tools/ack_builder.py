# src/tools/ack_builder.py

from src.frame_codec import build_mesh_frame, load_device_id
from src.serializers.ack_serializer import serialize_ack

def build_ack_frame(command_id: int, target_id: int, success: bool = True, status_code: int = 0,
                    src: int = None) -> bytes:
    src = src or load_device_id()
    payload = serialize_ack(command_id, status_code, is_ack=success)  # ✅ düzeltildi
    frame = build_mesh_frame('A', src, target_id, payload)
    return frame