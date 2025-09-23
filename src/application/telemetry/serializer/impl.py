from __future__ import annotations
# src/telemetry/serializer/impl.py

import struct

# -----------------------------------------------
# TELEMETRY SERIALIZATION FUNCTIONS
# -----------------------------------------------

def serialize_gps(lat: float, lon: float, alt: float) -> bytes:
    return struct.pack(">3f", lat, lon, alt)

def deserialize_gps(data: bytes) -> dict:
    lat, lon, alt = struct.unpack(">3f", data)
    return {"lat": lat, "lon": lon, "alt": alt}

def serialize_imu(roll: float, pitch: float, yaw: float) -> bytes:
    return struct.pack(">3f", roll, pitch, yaw)

def deserialize_imu(data: bytes) -> dict:
    roll, pitch, yaw = struct.unpack(">3f", data)
    return {"roll": roll, "pitch": pitch, "yaw": yaw}

def serialize_battery(voltage: float, current: float, level: float) -> bytes:
    return struct.pack(">3f", voltage, current, level)

def deserialize_battery(data: bytes) -> dict:
    voltage, current, level = struct.unpack(">3f", data)
    return {"voltage": voltage, "current": current, "level": level}

def serialize_heartbeat(mode: str, health: str, is_armed: bool, gps_fix: bool, sat_count: int) -> bytes:
    return (
        mode.encode("utf-8")[:32].ljust(32, b'\x00') +
        health.encode("utf-8")[:32].ljust(32, b'\x00') +
        struct.pack(">??B", is_armed, gps_fix, sat_count)
    )

def deserialize_heartbeat(data: bytes) -> dict:
    mode = data[:32].decode("utf-8").rstrip('\x00')
    health = data[32:64].decode("utf-8").rstrip('\x00')
    is_armed, gps_fix, sat_count = struct.unpack(">??B", data[64:67])
    return {
        "mode": mode,
        "health": health,
        "is_armed": is_armed,
        "gps_fix": gps_fix,
        "sat_count": sat_count
    }

def serialize_barometer(vertical_speed: float, ground_speed: float, altitude_relative: float) -> bytes:
    return struct.pack(">3f", vertical_speed, ground_speed, altitude_relative)

def deserialize_barometer(data: bytes) -> dict:
    vertical_speed, ground_speed, altitude_relative = struct.unpack(">3f", data)
    return {"vertical_speed": vertical_speed, "ground_speed": ground_speed, "altitude_relative": altitude_relative}

def serialize_ping(sequence: int) -> bytes:
    return struct.pack(">I", sequence)

def deserialize_ping(data: bytes) -> dict:
    sequence, = struct.unpack(">I", data)
    return {"sequence": sequence}