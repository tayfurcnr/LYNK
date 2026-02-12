from __future__ import annotations
# lynk/tools/command_builder.py

"""
Command Builder Module

Provides helper functions to construct mesh frames for various command types.
Each builder function corresponds to a specific command ID and serializes
its parameters before wrapping them in a mesh frame.
"""

import json
from typing import Any, Dict, Optional

from lynk.core.frame_codec import build_mesh_frame, load_device_id
from lynk.application.command.serializer.dispatcher import serialize_command


def build_cmd_frame(
    cmd_id: int,
    params: Optional[Dict[str, Any]] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a generic command mesh frame.

    Args:
        cmd_id (int): Command identifier.
        params (bytes, optional): Serialized command parameters (default: empty).
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, loaded from config.

    Returns:
        bytes: Complete mesh frame ready for transmission.
    """
    source = src if src is not None else load_device_id()
    payload = serialize_command(cmd_id, params, transaction_id=transaction_id)
    return build_mesh_frame('C', source, dst, payload, team_id=team_id)


def build_cmd_system_reboot(
    dst: int,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a SYSTEM_REBOOT command frame (no parameters).

    Args:
        dst (int): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for system_reboot command.
    """
    return build_cmd_frame(0x01, dst=dst, src=src, team_id=team_id, transaction_id=transaction_id)


def build_cmd_flight_set_mode(
    mode: str,
    dst: int,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a FLIGHT_SET_MODE command frame.

    Args:
        mode (str): Mode identifier.
        dst (int): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for flight_set_mode command.
    """
    return build_cmd_frame(0x15, {"mode": mode}, dst, src, team_id=team_id, transaction_id=transaction_id)


def build_cmd_flight_takeoff(
    altitude_m: float,
    min_pitch_deg: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a FLIGHT_TAKEOFF command frame.

    Args:
        altitude_m (float): Desired takeoff altitude in meters.
        min_pitch_deg (float | None): Optional minimum pitch angle.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for takeoff command.
    """
    params = {
        "altitude_m": altitude_m,
        "min_pitch_deg": min_pitch_deg if min_pitch_deg is not None else 0.0,
    }
    return build_cmd_frame(0x17, params, dst, src, team_id=team_id, transaction_id=transaction_id)


def build_cmd_flight_land(
    mode: int = 0,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    yaw: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a FLIGHT_LAND command frame with optional parameters.
    """
    has_target = target_lat is not None and target_lon is not None
    params = {
        "has_target": has_target,
        "mode": mode,
        "lat": target_lat if has_target else 0.0,
        "lon": target_lon if has_target else 0.0,
        "yaw": yaw if yaw is not None else 0.0,
    }
    return build_cmd_frame(0x1E, params, dst, src, team_id=team_id, transaction_id=transaction_id)

def build_cmd_flight_goto(
    lat: float,
    lon: float,
    alt: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a FLIGHT_GOTO command frame with target waypoint.

    Args:
        lat (float): Target latitude (float64).
        lon (float): Target longitude (float64).
        alt (float): Target altitude (float32).
        alt_ref (int | None): Altitude reference frame (optional).
    """
    params = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": alt_ref if alt_ref is not None else 0}
    return build_cmd_frame(0x18, params, dst, src, team_id=team_id, transaction_id=transaction_id)

def build_cmd_flight_set_speed(
    speed_mps: float,
    scope: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    params = {"speed_mps": speed_mps, "scope": scope if scope is not None else 0}
    return build_cmd_frame(0x19, params, dst, src, team_id=team_id, transaction_id=transaction_id)

def build_cmd_flight_set_altitude(
    alt_m: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    params = {"alt_m": alt_m, "alt_ref": alt_ref if alt_ref is not None else 0}
    return build_cmd_frame(0x1A, params, dst, src, team_id=team_id, transaction_id=transaction_id)

def build_cmd_flight_set_heading(
    mode: int,
    yaw_deg: float,
    turn: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    params = {"mode": mode, "yaw_deg": yaw_deg, "turn": turn if turn is not None else 0}
    return build_cmd_frame(0x1B, params, dst, src, transaction_id=transaction_id)

def build_cmd_flight_arming(
    arm: bool,
    force: bool = False,
    dst: int = 0xFF,
    src: Optional[int] = None,
    team_id: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a FLIGHT_ARMING command frame.

    Args:
        arm (bool): True to arm, False to disarm.
        force (bool): True to force the command.
        dst (int): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    params = {"arm": bool(arm), "force": bool(force)}
    return build_cmd_frame(0x16, params, dst, src, team_id=team_id, transaction_id=transaction_id)

def build_cmd_mission_upload(
    mission_id: int,
    waypoints: list,
    replace_existing: bool = True,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a MISSION_UPLOAD command frame.
    """
    payload = {
        "mission_id": mission_id,
        "waypoints": waypoints,
        "replace_existing": replace_existing
    }
    params = {"json": json.dumps(payload, separators=(',', ':'))}
    return build_cmd_frame(0x29, params, dst, src, transaction_id=transaction_id)


def build_cmd_mission_control(
    action: str,
    start_index: Optional[int] = None,
    abort_mode: Optional[str] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    """
    Build a MISSION_CONTROL command frame.
    """
    payload = {"action": action}
    if start_index is not None:
        payload["start_index"] = start_index
    if abort_mode is not None:
        payload["abort_mode"] = abort_mode
    
    params = {"json": json.dumps(payload, separators=(',', ':'))}
    return build_cmd_frame(0x2A, params, dst, src, transaction_id=transaction_id)

def build_cmd_flight_set_roi(
    roi_mode: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    alt_m: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    if roi_mode == 1 and (lat is None or lon is None):
        raise ValueError("lat and lon are required for ROI LOCATION mode")
    params = {
        "roi_mode": roi_mode,
        "lat": lat if lat is not None else 0.0,
        "lon": lon if lon is not None else 0.0,
        "alt_m": alt_m if alt_m is not None else 0.0,
    }
    return build_cmd_frame(0x1D, params, dst, src, transaction_id=transaction_id)

def build_cmd_flight_set_home(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    params = {
        "use_current": lat is None or lon is None,
        "lat": lat if lat is not None else 0.0,
        "lon": lon if lon is not None else 0.0,
    }
    return build_cmd_frame(0x1C, params, dst, src, transaction_id=transaction_id)

def build_cmd_system_set_vehicle_id(
    id: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x02, {"vehicle_id": id}, dst, src, transaction_id=transaction_id)

def build_cmd_system_set_team_id(
    team_id: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x03, {"team_id": team_id}, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_formation_execute(
    leader_id: int,
    formation_type: str,
    spacing_offset: Optional[float] = None,
    altitude_offset: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    payload = {
        "leader_id": leader_id,
        "formation_type": formation_type,
    }
    if spacing_offset is not None:
        payload["spacing_offset"] = spacing_offset
    if altitude_offset is not None:
        payload["altitude_offset"] = altitude_offset
    
    params = {"leader_id": leader_id, "formation_type": formation_type}
    if spacing_offset is not None:
        params["spacing_offset"] = spacing_offset
    if altitude_offset is not None:
        params["altitude_offset"] = altitude_offset
    return build_cmd_frame(0x3D, params, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_set_leader(
    leader_id: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x3E, {"leader_id": leader_id}, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_set_formation_type(
    formation_type: str,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x3F, {"formation_type": formation_type}, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_set_spacing(
    spacing_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x40, {"spacing_offset": spacing_offset}, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_set_altitude_offset(
    altitude_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x41, {"altitude_offset": altitude_offset}, dst, src, transaction_id=transaction_id)

def build_cmd_swarm_set_status(
    status: str,
    dst: int = 0xFF,
    src: Optional[int] = None,
    transaction_id: str = ""
) -> bytes:
    return build_cmd_frame(0x42, {"status": status}, dst, src, transaction_id=transaction_id)
