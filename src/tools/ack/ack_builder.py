# src/tools/ack/ack_builder.py

"""
ACK Builder Module

Constructs mesh frames for generic ACK/NACK responses to commands,
encapsulating the serialized acknowledgment payload.
"""

from typing import Optional

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.serializers.ack_serializer import serialize_ack


def build_ack_frame(
    command_id: int,
    target_id: int,
    success: bool = True,
    status_code: int = 0,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK or NACK mesh frame for a given command.

    Args:
        command_id (int): Identifier of the command being acknowledged.
        target_id (int): Destination node ID for the ACK/NACK.
        success (bool, optional): True to build an ACK, False for a NACK. Defaults to True.
        status_code (int, optional): Status or error code (default: 0 for SUCCESS).
        src (int | None, optional): Source device ID; if None, loaded via load_device_id().

    Returns:
        bytes: A type-'A' mesh frame containing the serialized ACK/NACK payload.
    """
    source = src if src is not None else load_device_id()
    payload = serialize_ack(command_id, status_code, is_ack=success)
    return build_mesh_frame('A', source, target_id, payload)
