from __future__ import annotations
# /src/telemetry/tools/builder.py

"""
Telemetry Builder Module

Provides functions to construct raw telemetry frames for different data types
by serializing payloads and encapsulating them in mesh frames. Each builder
function corresponds to a specific telemetry ID.
"""

from typing import Any, List, Optional

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.application.telemetry.definitions import telemetry_definitions

def build_tlm_frame(
    name: str,
    params: list,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Construct a generic telemetry mesh frame.

    Args:
        name (str): Telemetry name (e.g., "GPS").
        params (List[Any]): Ordered list of parameters matching the telemetry schema.
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, loaded from config.

    Returns:
        bytes: Complete mesh frame ready for transmission.
    """
    source_id = src if src is not None else load_device_id()

    for defn in telemetry_definitions.values():
        if defn.name == name:
            tlm_id = defn.id
            serializer = defn.serialize
            break
    else:
        raise ValueError(f"Telemetry name not found: {name}")

    # 🧩 ID'yi en başa ekle
    payload_body = serializer(*params)
    payload = bytes([tlm_id]) + payload_body

    return build_mesh_frame('T', source_id, dst, payload, team_id=team_id)


def build_tlm_gps(
    lat: float,
    lon: float,
    alt: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a GPS telemetry frame.

    Args:
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.
        alt (float): Altitude in meters.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized GPS data.
    """
    return build_tlm_frame("GPS", [lat, lon, alt], dst, src, team_id=team_id)


def build_tlm_imu(
    roll: float,
    pitch: float,
    yaw: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build an IMU telemetry frame.

    Args:
        roll (float): Roll angle in degrees.
        pitch (float): Pitch angle in degrees.
        yaw (float): Yaw angle in degrees.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized IMU data.
    """
    return build_tlm_frame("IMU", [roll, pitch, yaw], dst, src, team_id=team_id)


def build_tlm_battery(
    voltage: float,
    current: float,
    level: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a battery telemetry frame.

    Args:
        voltage (float): Battery voltage in volts.
        current (float): Current draw in amperes.
        level (float): Remaining battery percentage (0.0–100.0).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized battery data.
    """
    return build_tlm_frame("BATTERY", [voltage, current, level], dst, src, team_id=team_id)


def build_tlm_heartbeat(
    mode: str,
    health: str,
    is_armed: bool,
    gps_fix: bool,
    sat_count: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a heartbeat telemetry frame conveying system status.

    Args:
        mode (str): Flight mode identifier (e.g., "GUIDED").
        health (str): Health status (e.g., "OK" or "WARN").
        is_armed (bool): Whether the system is armed.
        gps_fix (bool): GPS fix status.
        sat_count (int): Number of satellites in view.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized heartbeat data.
    """
    return build_tlm_frame(
        "HEARTBEAT",
        [mode, health, is_armed, gps_fix, sat_count],
        dst,
        src,
        team_id=team_id
    )

def build_tlm_barometer(
    vertical_speed: float,
    ground_speed: float,
    altitude_relative: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a barometer telemetry frame.

    Args:
        vertical_speed (float): Vertical speed in m/s.
        ground speed (float): Ground speed of the vehicle in m/s.
        altitude_relative (float): Altitude relative to home in meters.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized barometer data.
    """
    return build_tlm_frame("BAROMETER", [vertical_speed, ground_speed, altitude_relative], dst, src, team_id=team_id)

def build_tlm_ping(
    sequence: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a ping telemetry frame.

    Args:
        sequence (int): A sequence number for the ping.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized ping data.
    """
    return build_tlm_frame("PING", [sequence], dst, src, team_id=team_id)