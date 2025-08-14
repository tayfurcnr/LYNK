from __future__ import annotations
# src/ack/serializer/dispatcher.py

import struct
from src.application.ack.definitions import ack_definitions
from src.shared.log.logger import logger

def serialize_ack(name: str, *params) -> bytes:
    """
    Serialize ACK data by ACK name.
    """
    for defn in ack_definitions.values():
        if defn.name == name:
            payload = defn.serialize(*params)
            frame = struct.pack(">B", defn.id) + payload
            logger.debug(f"[ACK] SERIALIZED | NAME: {name} | ID={defn.id} | SIZE={len(frame)}B")
            return frame
    raise ValueError(f"ACK name not found: {name}")

def deserialize_ack(payload: bytes) -> dict:
    """
    Deserialize an ACK frame using its ID.

    Returns:
        dict: {"ack_id": int, "name": str, ...fields }
    """
    if not payload or len(payload) < 1:
        raise ValueError("Payload too short")

    aid = payload[0]
    data = payload[1:]

    defn = ack_definitions.get(aid)
    if not defn:
        raise ValueError(f"Unknown ACK ID: {aid}")

    fields = defn.deserialize(data)
    logger.debug(
        f"[ACK] DESERIALIZED | NAME: {defn.name} | ID=0x{aid:02X} | FIELDS={list(fields.keys())}"
    )

    return {
    "ack_id": aid,
    **fields
}