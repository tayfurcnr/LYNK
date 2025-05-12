# src/tools/command_builder.py

"""
Command Builder Module

Provides helper functions to construct mesh frames for various command types.
Each builder function corresponds to a specific command ID and serializes
its parameters before wrapping them in a mesh frame.
"""

import struct
from typing import Any, List, Optional

from src.core.frame_codec import build_mesh_frame, load_device_id
from src.serializers.command_serializer import serialize_command


def build_cmd_frame(
    cmd_id: int,
    params: bytes = b'',
    dst: int = 0xFF,
    src: Optional[int] = None
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
    payload = serialize_command(cmd_id, params)
    return build_mesh_frame('C', source, dst, payload)


def build_cmd_reboot(
    dst: int,
    src: Optional[int] = None
) -> bytes:
    """
    Build a REBOOT command frame (no parameters).

    Args:
        dst (int): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for reboot command.
    """
    return build_cmd_frame(0x01, dst=dst, src=src)


def build_cmd_set_mode(
    mode: int,
    dst: int,
    src: Optional[int] = None
) -> bytes:
    """
    Build a SET_MODE command frame.

    Args:
        mode (int): Mode identifier.
        dst (int): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for set-mode command.
    """
    params = struct.pack(">B", mode)
    return build_cmd_frame(0x02, params, dst, src)


def build_cmd_takeoff(
    takeoff_alt: float,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    target_alt: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a TAKEOFF command frame. Includes optional target coordinates.

    Args:
        takeoff_alt (float): Desired takeoff altitude in meters.
        target_lat (float | None): Target latitude (optional).
        target_lon (float | None): Target longitude (optional).
        target_alt (float | None): Target altitude (optional).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for takeoff command.
    """
    if None not in (target_lat, target_lon, target_alt):
        # pack four floats: takeoff_alt, lat, lon, alt
        params = struct.pack(">ffff", takeoff_alt, target_lat, target_lon, target_alt)
    else:
        # only takeoff altitude
        params = struct.pack(">f", takeoff_alt)
    return build_cmd_frame(0x03, params, dst, src)


def build_cmd_landing(
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a LANDING command frame with optional landing coordinates.

    Args:
        target_lat (float | None): Landing latitude (optional).
        target_lon (float | None): Landing longitude (optional).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for landing command.
    """
    if target_lat is not None and target_lon is not None:
        params = struct.pack(">ff", target_lat, target_lon)
    else:
        params = b''
    return build_cmd_frame(0x04, params, dst, src)


def build_cmd_gimbal(
    yaw: float,
    pitch: float,
    roll: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a GIMBAL command frame to orient camera gimbal.

    Args:
        yaw (float): Yaw angle in degrees.
        pitch (float): Pitch angle in degrees.
        roll (float): Roll angle in degrees.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for gimbal command.
    """
    params = struct.pack(">fff", yaw, pitch, roll)
    return build_cmd_frame(0x05, params, dst, src)


def build_cmd_goto(
    target_lat: float,
    target_lon: float,
    target_alt: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a GOTO command frame with target waypoint.

    Args:
        target_lat (float): Target latitude.
        target_lon (float): Target longitude.
        target_alt (float): Target altitude.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for goto command.
    """
    params = struct.pack(">fff", target_lat, target_lon, target_alt)
    return build_cmd_frame(0x06, params, dst, src)


def build_cmd_simple_follow_me(
    target_id: int,
    altitude: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a SIMPLE_FOLLOW_ME command frame.

    Args:
        target_id (int): ID of the device to follow.
        altitude (float | None): Follow altitude (optional).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for follow-me command.
    """
    if altitude is not None:
        params = struct.pack(">If", target_id, altitude)
    else:
        params = struct.pack(">I", target_id)
    return build_cmd_frame(0x07, params, dst, src)


def build_cmd_waypoints(
    waypoints: List[tuple[float, float, float]],
    dst: int = 0xFF,
    src: Optional[int] = None
) -> bytes:
    """
    Build a WAYPOINTS command frame containing multiple waypoints.

    Args:
        waypoints (List[tuple[float, float, float]]): Sequence of (lat, lon, alt).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.

    Returns:
        bytes: Mesh frame for waypoints command.
    """
    params = b''.join(
        struct.pack(">fff", lat, lon, alt)
        for lat, lon, alt in waypoints
    )
    return build_cmd_frame(0x09, params, dst, src)
