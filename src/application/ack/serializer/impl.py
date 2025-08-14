from __future__ import annotations
# src/ack/serializer/impl.py

import struct

# -----------------------------------------------
# ACK SERIALIZATION FUNCTIONS
# -----------------------------------------------

def serialize_ack_ok(message: str) -> bytes:
    return message.encode("utf-8")[:64].ljust(64, b'\x00')

def deserialize_ack_ok(data: bytes) -> dict:
    message = data[:64].decode("utf-8").rstrip('\x00')
    return {"message": message}

def serialize_ack_error(message: str) -> bytes:
    return message.encode("utf-8")[:64].ljust(64, b'\x00')

def deserialize_ack_error(data: bytes) -> dict:
    message = data[:64].decode("utf-8").rstrip('\x00')
    return {"message": message}

def serialize_ack_busy(message: str) -> bytes:
    return message.encode("utf-8")[:64].ljust(64, b'\x00')

def deserialize_ack_busy(data: bytes) -> dict:
    message = data[:64].decode("utf-8").rstrip('\x00')
    return {"message": message}

def serialize_ack_invalid_cmd(message: str) -> bytes:
    return message.encode("utf-8")[:64].ljust(64, b'\x00')

def deserialize_ack_invalid_cmd(data: bytes) -> dict:
    message = data[:64].decode("utf-8").rstrip('\x00')
    return {"message": message}