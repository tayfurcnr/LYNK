from __future__ import annotations
# src/application/command/tools/dispatcher.py

"""
Command Dispatcher Module

Defines high‐level command functions that build and send specific command frames
over a communication interface, while logging each action.
"""

import struct
from typing import Any, List, Optional, Protocol

from src.application.command.tools.builder import (
    build_cmd_system_reboot,
    build_cmd_flight_set_mode,
    build_cmd_flight_takeoff,
    build_cmd_flight_goto,
    build_cmd_flight_set_speed,
    build_cmd_flight_set_altitude,
    build_cmd_flight_set_heading,
    build_cmd_flight_set_home,
    build_cmd_flight_set_roi,
    build_cmd_flight_land,
    build_cmd_flight_arming,
    build_cmd_system_set_vehicle_id,
    build_cmd_system_set_team_id,
    build_cmd_mission_upload, 
    build_cmd_mission_control,
    build_cmd_swarm_formation_execute,
    build_cmd_swarm_set_leader,
    build_cmd_swarm_set_formation_type,
    build_cmd_swarm_set_spacing,
    build_cmd_swarm_set_altitude_offset,
    build_cmd_swarm_set_status
)
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger
from src.application.ack.tools.dispatcher import send_ack_ok, send_ack_invalid_cmd
from src.application.command.tools.cache import set_last_command


class SendableInterface(Protocol):
    """
    Protocol for a communication interface that supports send().
    """
    def send(self, frame: bytes) -> None: ...


def cmd_system_reboot(
    interface: SendableInterface,
    dst: int,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a SYSTEM_REBOOT command to reset the target device.

    Args:
        interface: Communication interface instance.
        dst (int): Destination device ID.
        src (int | None): Optional source device ID.
    """
    frame = build_cmd_system_reboot(dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.info(f"[COMMAND] SENT | SYSTEM_REBOOT -> {target}")


def cmd_flight_set_mode(
    interface: SendableInterface,
    mode: str,
    dst: int,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a FLIGHT_SET_MODE command to change the flight mode.

    Args:
        interface: Communication interface instance.
        mode (str): Mode identifier.
        dst (int): Destination device ID.
        src (int | None): Optional source device ID.
    """
    frame = build_cmd_flight_set_mode(mode, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_MODE({mode}) -> {target}")


def cmd_flight_arming(
    interface: SendableInterface,
    arm: bool,
    force: bool = False,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a FLIGHT_ARMING command.

    Args:
        interface: Communication interface instance.
        arm (bool): True to arm, False to disarm.
        force (bool): True to force the command.
        dst (int): Destination device ID.
        src (int | None): Optional source device ID.
    """
    frame = build_cmd_flight_arming(arm, force, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.info(f"[COMMAND] SENT | FLIGHT_ARMING(arm={arm}, force={force}) -> {target}")


def cmd_flight_takeoff(
    interface: SendableInterface,
    altitude_m: float,
    min_pitch_deg: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a FLIGHT_TAKEOFF command.

    Args:
        interface: Communication interface instance.
        altitude_m (float): Takeoff altitude in meters.
        min_pitch_deg (float | None): Optional minimum pitch angle.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_flight_takeoff(altitude_m, min_pitch_deg, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.info(f"[COMMAND] SENT | FLIGHT_TAKEOFF(alt={altitude_m}) -> {target}")


def cmd_flight_land(
    interface: SendableInterface,
    mode: int = 0,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    yaw: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a FLIGHT_LAND command, optionally with landing coordinates and yaw.

    Args:
        interface: Communication interface instance.
        ...
    """
    frame = build_cmd_flight_land(mode, target_lat, target_lon, yaw, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.info(f"[COMMAND] SENT | FLIGHT_LAND -> {target}")


def cmd_flight_goto(
    interface: SendableInterface,
    lat: float,
    lon: float,
    alt: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a FLIGHT_GOTO command to navigate to a waypoint.

    Args:
        interface: Communication interface instance.
        lat (float): Target latitude.
        lon (float): Target longitude.
        alt (float): Target altitude.
        alt_ref (int | None): Altitude reference frame.
    """
    frame = build_cmd_flight_goto(lat, lon, alt, alt_ref, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_GOTO(lat={lat:.6f}, lon={lon:.6f}, alt={alt}) -> DST: {dst}")

def cmd_flight_set_speed(
    interface: SendableInterface,
    speed_mps: float,
    scope: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_flight_set_speed(speed_mps, scope, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_SPEED({speed_mps}) -> DST: {dst}")

def cmd_flight_set_altitude(
    interface: SendableInterface,
    alt_m: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_flight_set_altitude(alt_m, alt_ref, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_ALTITUDE({alt_m}) -> DST: {dst}")

def cmd_flight_set_heading(
    interface: SendableInterface,
    mode: int,
    yaw_deg: float,
    turn: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_flight_set_heading(mode, yaw_deg, turn, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_HEADING(mode={mode}, yaw={yaw_deg}) -> DST: {dst}")

def cmd_flight_set_roi(
    interface: SendableInterface,
    roi_mode: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    alt_m: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_flight_set_roi(roi_mode, lat, lon, alt_m, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_ROI(mode={roi_mode}) -> DST: {dst}")

def cmd_flight_set_home(
    interface: SendableInterface,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_flight_set_home(lat, lon, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FLIGHT_SET_HOME(lat={lat}, lon={lon}) -> DST: {dst}")

def cmd_mission_upload(
    interface: SendableInterface,
    mission_id: int,
    waypoints: list,
    replace_existing: bool = True,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a MISSION_UPLOAD command.
    """
    frame = build_cmd_mission_upload(mission_id, waypoints, replace_existing, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | MISSION_UPLOAD(id={mission_id}, wps={len(waypoints)}) -> DST: {dst}")


def cmd_mission_control(
    interface: SendableInterface,
    action: str,
    start_index: Optional[int] = None,
    abort_mode: Optional[str] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a MISSION_CONTROL command.
    """
    frame = build_cmd_mission_control(action, start_index, abort_mode, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | MISSION_CONTROL(action={action}) -> DST: {dst}")

def cmd_system_set_vehicle_id(
    interface: SendableInterface,
    id: int,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_system_set_vehicle_id(id, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SYSTEM_SET_VEHICLE_ID({id}) -> DST: {dst}")

def cmd_system_set_team_id(
    interface: SendableInterface,
    team_id: int,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_system_set_team_id(team_id, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SYSTEM_SET_TEAM_ID({team_id}) -> DST: {dst}")

def cmd_swarm_formation_execute(
    interface: SendableInterface,
    leader_id: int,
    formation_type: str,
    spacing_offset: Optional[float] = None,
    altitude_offset: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_formation_execute(leader_id, formation_type, spacing_offset, altitude_offset, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_FORMATION_EXECUTE -> DST: {dst}")

def cmd_swarm_set_leader(
    interface: SendableInterface,
    leader_id: int,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_set_leader(leader_id, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_SET_LEADER({leader_id}) -> DST: {dst}")

def cmd_swarm_set_formation_type(
    interface: SendableInterface,
    formation_type: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_set_formation_type(formation_type, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_SET_FORMATION_TYPE({formation_type}) -> DST: {dst}")

def cmd_swarm_set_spacing(
    interface: SendableInterface,
    spacing_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_set_spacing(spacing_offset, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_SET_SPACING({spacing_offset}) -> DST: {dst}")

def cmd_swarm_set_altitude_offset(
    interface: SendableInterface,
    altitude_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_set_altitude_offset(altitude_offset, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_SET_ALTITUDE_OFFSET({altitude_offset}) -> DST: {dst}")

def cmd_swarm_set_status(
    interface: SendableInterface,
    status: str,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    frame = build_cmd_swarm_set_status(status, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SWARM_SET_STATUS({status}) -> DST: {dst}")
