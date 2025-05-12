# src/tools//telemetry/telemetry_builder.py

"""
Telemetry Builder Module

Provides functions to construct raw telemetry frames for different data types
by serializing payloads and encapsulating them in mesh frames. Each builder
function corresponds to a specific telemetry ID.
"""

from typing import Any, List, Optional

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.serializers.telemetry_serializer import serialize_telemetry


def build_tlm_frame(
    tlm_id: int,
    params: List[Any],
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Construct a generic telemetry mesh frame.

    Args:
        tlm_id (int): Telemetry identifier (e.g., 0x01 for GPS).
        params (List[Any]): Ordered list of parameters matching the telemetry schema.
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, loaded from config.

    Returns:
        bytes: Complete mesh frame ready for transmission.
    """
    source_id = src if src is not None else load_device_id()
    payload = serialize_telemetry(tlm_id, *params)
    return build_mesh_frame('T', source_id, dst, payload)


def build_tlm_gps(
    lat: float,
    lon: float,
    alt: float,
    dst: int = 0xFF,
    src: Optional[int] = None
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
    return build_tlm_frame(0x01, [lat, lon, alt], dst, src)


def build_tlm_imu(
    roll: float,
    pitch: float,
    yaw: float,
    dst: int = 0xFF,
    src: Optional[int] = None
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
    return build_tlm_frame(0x02, [roll, pitch, yaw], dst, src)


def build_tlm_battery(
    voltage: float,
    current: float,
    level: float,
    dst: int = 0xFF,
    src: Optional[int] = None
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
    return build_tlm_frame(0x03, [voltage, current, level], dst, src)


def build_tlm_heartbeat(
    mode: str,
    health: str,
    is_armed: bool,
    gps_fix: bool,
    sat_count: int,
    dst: int = 0xFF,
    src: Optional[int] = None
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
        0x04,
        [mode, health, is_armed, gps_fix, sat_count],
        dst,
        src
    )
