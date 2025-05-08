import struct
from src.tools.log.logger import logger

# 🔹 TELEMETRY_CODECS maps each telemetry type ID (tlm_id) to its
# corresponding serialization and deserialization logic.
# This allows modular handling of multiple telemetry types.

TELEMETRY_CODECS = {
    0x01: {  # GPS (latitude, longitude, altitude)
        "serialize": lambda *p: struct.pack(">3f", *p),
        "deserialize": lambda data: dict(zip(["lat", "lon", "alt"], struct.unpack(">3f", data)))
    },
    0x02: {  # IMU (roll, pitch, yaw)
        "serialize": lambda *p: struct.pack(">3f", *p),
        "deserialize": lambda data: dict(zip(["roll", "pitch", "yaw"], struct.unpack(">3f", data)))
    },
    0x03: {  # BATTERY (voltage, current, level)
        "serialize": lambda *p: struct.pack(">3f", *p),
        "deserialize": lambda data: dict(zip(["voltage", "current", "level"], struct.unpack(">3f", data)))
    },
    0x04: {  # HEARTBEAT (mode:str, health:str, is_armed:bool, gps_fix:bool, sat_count:int)
        "serialize": lambda *p: (
            p[0].encode("utf-8")[:32].ljust(32, b'\x00') +  # mode (32 bytes)
            p[1].encode("utf-8")[:32].ljust(32, b'\x00') +  # health (32 bytes)
            struct.pack(">??B", *p[2:])                    # is_armed, gps_fix, sat_count
        ),
        "deserialize": lambda data: {
            "mode": data[:32].decode("utf-8").rstrip('\x00'),
            "health": data[32:64].decode("utf-8").rstrip('\x00'),
            **dict(zip(
                ["is_armed", "gps_fix", "sat_count"],
                struct.unpack(">??B", data[64:67])
            ))
        }
    }
}


def serialize_telemetry(tlm_id: int, *params) -> bytes:
    """
    Serializes telemetry data based on telemetry type ID.

    Parameters:
        tlm_id (int): Telemetry Type ID (e.g., 0x01 = GPS, 0x04 = HEARTBEAT)
        *params (tuple): Ordered parameters to serialize for the given type.
                         - GPS: (lat, lon, alt)
                         - IMU: (roll, pitch, yaw)
                         - BATTERY: (voltage, current, level)
                         - HEARTBEAT: (mode, health, is_armed, gps_fix, sat_count, timestamp)

    Returns:
        bytes: Serialized byte stream (1 byte tlm_id + payload)
    """
    if tlm_id not in TELEMETRY_CODECS:
        raise ValueError(f"Unsupported telemetry type ID: {tlm_id}")

    payload = TELEMETRY_CODECS[tlm_id]["serialize"](*params)
    full_frame = struct.pack(">B", tlm_id) + payload

    logger.debug(
        f"[TELEMETRY] SERIALIZED | TLM_ID: {tlm_id} | PARAMS: {params} | SIZE: {len(full_frame)}B"
    )
    return full_frame


def deserialize_telemetry(payload: bytes) -> dict:
    """
    Deserializes a telemetry byte stream into a structured dictionary.

    Parameters:
        payload (bytes): Byte stream containing telemetry type ID + binary payload.

    Returns:
        dict: Dictionary containing 'tlm_id' and all parsed telemetry fields.
              Example for GPS: {'tlm_id': 1, 'lat': ..., 'lon': ..., 'alt': ...}
    """
    tlm_id = payload[0]
    data = payload[1:]

    if tlm_id not in TELEMETRY_CODECS:
        raise ValueError(f"Unsupported telemetry type ID: {tlm_id}")

    decoded = TELEMETRY_CODECS[tlm_id]["deserialize"](data)

    logger.debug(
        f"[TELEMETRY] DESERIALIZED | TLM_ID: {tlm_id} | FIELDS: {list(decoded.keys())} | SIZE: {len(payload)}B"
    )

    result = {"tlm_id": tlm_id}
    result.update(decoded)
    return result
