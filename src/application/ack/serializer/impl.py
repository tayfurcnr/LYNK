from __future__ import annotations
# src/ack/serializer/impl.py

import struct

# -----------------------------------------------
# ACK SERIALIZATION FUNCTIONS
# Payload: cmd_id (H, 2B)
# -----------------------------------------------

def serialize_ack_ok(cmd_id: int) -> bytes:
    """Serializes an ACK_OK with only the command ID it refers to."""
    return struct.pack(">H", cmd_id)

def deserialize_ack_ok(data: bytes) -> dict:
    """Deserializes an ACK_OK and extracts the command ID."""
    cmd_id, = struct.unpack(">H", data)
    return {"cmd_id": cmd_id}

def serialize_ack_error(cmd_id: int) -> bytes:
    """Serializes an ACK_ERROR with only the command ID it refers to."""
    return struct.pack(">H", cmd_id)

def deserialize_ack_error(data: bytes) -> dict:
    """Deserializes an ACK_ERROR and extracts the command ID."""
    cmd_id, = struct.unpack(">H", data)
    return {"cmd_id": cmd_id}

def serialize_ack_busy(cmd_id: int) -> bytes:
    """Serializes an ACK_BUSY with only the command ID it refers to."""
    return struct.pack(">H", cmd_id)

def deserialize_ack_busy(data: bytes) -> dict:
    """Deserializes an ACK_BUSY and extracts the command ID."""
    cmd_id, = struct.unpack(">H", data)
    return {"cmd_id": cmd_id}

def serialize_ack_invalid_cmd(cmd_id: int) -> bytes:
    """Serializes an ACK_INVALID_CMD with only the command ID it refers to."""
    return struct.pack(">H", cmd_id)

def deserialize_ack_invalid_cmd(data: bytes) -> dict:
    """Deserializes an ACK_INVALID_CMD and extracts the command ID."""
    cmd_id, = struct.unpack(">H", data)
    return {"cmd_id": cmd_id}
