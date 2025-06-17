# /src/ack/tools/builder.py

"""
ACK Builder Module

Provides functions to construct raw ACK frames for different data types
by serializing payloads and encapsulating them in mesh frames. Each builder
function corresponds to a specific ACK ID.
"""

from typing import Any, List, Optional

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.ack.definitions import ack_definitions

def build_ack_frame(
    name: str,
    params: list,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Construct a generic ACK mesh frame.

    Args:
        name (str): ACK name (e.g., "ACK_OK").
        params (List[Any]): Ordered list of parameters matching the ACK schema.
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, loaded from config.

    Returns:
        bytes: Complete mesh frame ready for transmission.
    """
    source_id = src if src is not None else load_device_id()

    for defn in ack_definitions.values():
        if defn.name == name:
            ack_id = defn.id
            serializer = defn.serialize
            break
    else:
        raise ValueError(f"ACK name not found: {name}")

    # 🧩 ID'yi en başa ekle
    payload_body = serializer(*params)
    payload = bytes([ack_id]) + payload_body

    return build_mesh_frame('A', source_id, dst, payload)


def build_ack_ok(
    message: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK_OK frame.
    """
    return build_ack_frame("ACK_OK", [message], dst, src)


def build_ack_error(
    message: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK_ERROR frame.
    """
    return build_ack_frame("ACK_ERROR", [message], dst, src)


def build_ack_busy(
    message: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK_BUSY frame.
    """
    return build_ack_frame("ACK_BUSY", [message], dst, src)


def build_ack_invalid_cmd(
    message: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build an ACK_INVALID_CMD frame.
    """
    return build_ack_frame("ACK_INVALID_CMD", [message], dst, src)