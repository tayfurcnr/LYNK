# src/tools/command_dispatcher.py

"""
Command Dispatcher Module

Defines high‐level command functions that build and send specific command frames
over a communication interface, while logging each action.
"""

from typing import Any, List, Optional, Protocol

from src.tools.command.command_builder import (
    build_cmd_reboot,
    build_cmd_set_mode,
    build_cmd_takeoff,
    build_cmd_landing,
    build_cmd_gimbal,
    build_cmd_goto,
    build_cmd_simple_follow_me,
    build_cmd_waypoints
)
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger


class SendableInterface(Protocol):
    """
    Protocol for a communication interface that supports send().
    """
    def send(self, frame: bytes) -> None: ...


def cmd_reboot(
    interface: SendableInterface,
    dst: int,
    src: Optional[int] = None
) -> None:
    """
    Send a REBOOT command to reset the target device.

    Args:
        interface: Communication interface instance.
        dst (int): Destination device ID.
        src (int | None): Optional source device ID.
    """
    frame = build_cmd_reboot(dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | REBOOT -> DST: {dst}")


def cmd_set_mode(
    interface: SendableInterface,
    mode: int,
    dst: int,
    src: Optional[int] = None
) -> None:
    """
    Send a SET_MODE command to change the flight mode.

    Args:
        interface: Communication interface instance.
        mode (int): Mode identifier.
        dst (int): Destination device ID.
        src (int | None): Optional source device ID.
    """
    frame = build_cmd_set_mode(mode, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SET_MODE({mode}) -> DST: {dst}")


def cmd_takeoff(
    interface: SendableInterface,
    takeoff_alt: float,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    target_alt: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a TAKEOFF command, optionally with target coordinates.

    Args:
        interface: Communication interface instance.
        takeoff_alt (float): Takeoff altitude in meters.
        target_lat (float | None): Optional latitude of target.
        target_lon (float | None): Optional longitude of target.
        target_alt (float | None): Optional altitude of target.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_takeoff(
        takeoff_alt, target_lat, target_lon, target_alt, dst, src
    )
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | TAKEOFF({takeoff_alt}) -> DST: {dst}")


def cmd_landing(
    interface: SendableInterface,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a LANDING command, optionally with landing coordinates.

    Args:
        interface: Communication interface instance.
        target_lat (float | None): Optional landing latitude.
        target_lon (float | None): Optional landing longitude.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_landing(target_lat, target_lon, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | LANDING -> DST: {dst}")


def cmd_gimbal(
    interface: SendableInterface,
    yaw: float,
    pitch: float,
    roll: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a GIMBAL command to orient the camera gimbal.

    Args:
        interface: Communication interface instance.
        yaw (float): Yaw angle in degrees.
        pitch (float): Pitch angle in degrees.
        roll (float): Roll angle in degrees.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_gimbal(yaw, pitch, roll, dst, src)
    send_frame(interface, frame)
    logger.info(
        f"[COMMAND] SENT | GIMBAL(yaw={yaw:.1f}, pitch={pitch:.1f}, roll={roll:.1f}) -> DST: {dst}"
    )


def cmd_goto(
    interface: SendableInterface,
    target_lat: float,
    target_lon: float,
    target_alt: float,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a GOTO command to navigate to a waypoint.

    Args:
        interface: Communication interface instance.
        target_lat (float): Target latitude.
        target_lon (float): Target longitude.
        target_alt (float): Target altitude.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_goto(target_lat, target_lon, target_alt, dst, src)
    send_frame(interface, frame)
    logger.info(
        f"[COMMAND] SENT | GOTO(lat={target_lat:.5f}, lon={target_lon:.5f}, alt={target_alt}) -> DST: {dst}"
    )


def cmd_simple_follow_me(
    interface: SendableInterface,
    target_id: int,
    altitude: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a SIMPLE_FOLLOW_ME command to follow another device.

    Args:
        interface: Communication interface instance.
        target_id (int): ID of the device to follow.
        altitude (float | None): Optional follow altitude.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_simple_follow_me(target_id, altitude, dst, src)
    send_frame(interface, frame)
    logger.info(
        f"[COMMAND] SENT | FOLLOW_ME(target={target_id}, alt={altitude}) -> DST: {dst}"
    )


def cmd_waypoints(
    interface: SendableInterface,
    waypoints: List[tuple[float, float, float]],
    dst: int = 0xFF,
    src: Optional[int] = None
) -> None:
    """
    Send a WAYPOINTS command containing multiple waypoints.

    Args:
        interface: Communication interface instance.
        waypoints (List[tuple[float, float, float]]): Sequence of (lat, lon, alt).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_cmd_waypoints(waypoints, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | WAYPOINTS(count={len(waypoints)}) -> DST: {dst}")
