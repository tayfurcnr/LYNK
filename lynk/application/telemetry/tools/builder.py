from __future__ import annotations
# /lynk/telemetry/tools/builder.py

"""
Telemetry Builder Module

Provides functions to construct raw telemetry frames for different data types
by serializing payloads and encapsulating them in mesh frames. Each builder
function corresponds to a specific telemetry ID.
"""

from typing import Any, List, Optional

from lynk.core.frame_codec import build_mesh_frame, load_device_id
from lynk.application.telemetry.serializer.dispatcher import serialize_telemetry

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

    payload = serialize_telemetry(name, *params)

    return build_mesh_frame('T', source_id, dst, payload, team_id=team_id)


def build_tlm_gps(
    lat: float,
    lon: float,
    alt_m: float,
    rel_alt_m: float = 0.0,
    fix_type: int = 3,
    sat_count: int = 0,
    hdop: float = 1.0,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a GPS telemetry frame.

    Args:
        lat (float): Latitude in decimal degrees (double precision).
        lon (float): Longitude in decimal degrees (double precision).
        alt_m (float): Altitude in meters (MSL).
        rel_alt_m (float): Relative altitude above home in meters.
        fix_type (int): GPS fix type (0-8).
        sat_count (int): Satellites visible.
        hdop (float): HDOP value.
        timestamp_ms (int): Unix epoch time in ms.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized GPS data.
    """
    params = [lat, lon, alt_m, rel_alt_m, fix_type, sat_count, hdop, timestamp_ms]
    return build_tlm_frame("GPS", params, dst, src, team_id=team_id)



def build_tlm_attitude(
    roll_deg: float,
    pitch_deg: float,
    yaw_deg: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build an Attitude telemetry frame.

    Args:
        roll_deg (float): Roll angle in degrees.
        pitch_deg (float): Pitch angle in degrees.
        yaw_deg (float): Yaw angle in degrees.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized attitude data.
    """
    return build_tlm_frame("ATTITUDE", [roll_deg, pitch_deg, yaw_deg, timestamp_ms], dst, src, team_id=team_id)


def build_tlm_battery(
    voltage_v: float,
    current_a: float,
    level_pct: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a battery telemetry frame.

    Args:
        voltage_v (float): Battery voltage in volts.
        current_a (float): Current draw in amperes.
        level_pct (float): Remaining battery percentage (0.0–100.0).
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized battery data.
    """
    return build_tlm_frame("BATTERY", [voltage_v, current_a, level_pct, timestamp_ms], dst, src, team_id=team_id)


def build_tlm_state(
    mode: str,
    is_armed: bool,
    connected: bool = True,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a state telemetry frame conveying vehicle status (MAVROS-aligned).

    Args:
        mode (str): Flight mode identifier (e.g., "STABILIZE", "GUIDED").
        is_armed (bool): Whether the vehicle is armed.
        connected (bool): FCU connection status (default: True).
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized state data.
    """
    return build_tlm_frame(
        "STATE",
        [mode, is_armed, connected, timestamp_ms],
        dst,
        src,
        team_id=team_id
    )


def build_tlm_vfr_hud(
    airspeed_ms: float,
    groundspeed_ms: float,
    heading_deg: float,
    throttle: float,
    alt_m: float,
    climb_ms: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a VFR_HUD telemetry frame (MAVROS-aligned).

    Args:
        airspeed_ms (float): Airspeed in m/s.
        groundspeed_ms (float): Ground speed in m/s.
        heading_deg (float): Heading in degrees (0-360).
        throttle (float): Throttle percentage (0.0-1.0).
        alt_m (float): Altitude in meters (MSL).
        climb_ms (float): Climb rate in m/s.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized VFR_HUD data.
    """
    params = [airspeed_ms, groundspeed_ms, heading_deg, throttle, alt_m, climb_ms, timestamp_ms]
    return build_tlm_frame("VFR_HUD", params, dst, src, team_id=team_id)

def build_tlm_heartbeat(
    sequence: int,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None
) -> bytes:
    """
    Build a heartbeat telemetry frame.

    Args:
        sequence (int): A sequence number for the heartbeat.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame containing serialized heartbeat data.
    """
    return build_tlm_frame("HEARTBEAT", [sequence, timestamp_ms], dst, src, team_id=team_id)
