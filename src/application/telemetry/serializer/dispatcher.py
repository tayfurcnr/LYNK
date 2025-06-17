# src/application/telemetry/serializer/dispatcher.py

import struct
from src.application.telemetry.definitions import telemetry_definitions
from src.shared.log.logger import logger

def serialize_telemetry(name: str, *params) -> bytes:
    """
    Serialize telemetry data by telemetry name.
    """
    for defn in telemetry_definitions.values():
        if defn.name == name:
            payload = defn.serialize(*params)
            frame = struct.pack(">B", defn.id) + payload
            logger.debug(f"[TELEMETRY] SERIALIZED | NAME: {name} | ID={defn.id} | SIZE={len(frame)}B")
            return frame
    raise ValueError(f"Telemetry name not found: {name}")

def deserialize_telemetry(payload: bytes) -> dict:
    """
    Deserialize a telemetry frame using its ID.

    Returns:
        dict: {"tlm_id": int, "name": str, ...fields }
    """
    if not payload or len(payload) < 1:
        raise ValueError("Payload too short")

    tid = payload[0]
    data = payload[1:]

    defn = telemetry_definitions.get(tid)
    if not defn:
        raise ValueError(f"Unknown telemetry ID: {tid}")

    fields = defn.deserialize(data)
    logger.debug(
        f"[TELEMETRY] DESERIALIZED | NAME: {defn.name} | ID=0x{tid:02X} | FIELDS={list(fields.keys())}"
    )

    return {
    "tlm_id": tid,
    **fields
}