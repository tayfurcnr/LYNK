# src/tools/command_dispatcher.py

from src.tools.command_builder import (
    build_cmd_reboot,
    build_cmd_set_mode,
    build_cmd_takeoff,
    build_cmd_landing,
    build_cmd_gimbal,
    build_cmd_goto,
    build_cmd_simple_follow_me,
    build_cmd_waypoints
)
from src.tools.transmitter import send_frame
from src.tools.logger import logger


def cmd_reboot(interface, dst: int, src: int = None):
    frame = build_cmd_reboot(dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | REBOOT -> DST: {dst}")


def cmd_set_mode(interface, mode: int, dst: int, src: int = None):
    frame = build_cmd_set_mode(mode, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | SET_MODE({mode}) -> DST: {dst}")


def cmd_takeoff(interface, takeoff_alt: float,
                target_lat: float = None, target_lon: float = None, target_alt: float = None,
                dst: int = 0xFF, src: int = None):
    frame = build_cmd_takeoff(takeoff_alt, target_lat, target_lon, target_alt, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | TAKEOFF({takeoff_alt}) -> DST: {dst}")


def cmd_landing(interface, target_lat: float = None, target_lon: float = None,
                dst: int = 0xFF, src: int = None):
    frame = build_cmd_landing(target_lat, target_lon, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | LANDING -> DST: {dst}")


def cmd_gimbal(interface, yaw: float, pitch: float, roll: float,
               dst: int = 0xFF, src: int = None):
    frame = build_cmd_gimbal(yaw, pitch, roll, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | GIMBAL({yaw:.1f}, {pitch:.1f}, {roll:.1f}) -> DST: {dst}")


def cmd_goto(interface, target_lat: float, target_lon: float, target_alt: float,
             dst: int = 0xFF, src: int = None):
    frame = build_cmd_goto(target_lat, target_lon, target_alt, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | GOTO({target_lat:.5f}, {target_lon:.5f}, {target_alt}) -> DST: {dst}")


def cmd_simple_follow_me(interface, target_id: int, altitude: float = None,
                         dst: int = 0xFF, src: int = None):
    frame = build_cmd_simple_follow_me(target_id, altitude, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | FOLLOW_ME(Target: {target_id}, Alt: {altitude}) -> DST: {dst}")


def cmd_waypoints(interface, waypoints: list,
                  dst: int = 0xFF, src: int = None):
    frame = build_cmd_waypoints(waypoints, dst, src)
    send_frame(interface, frame)
    logger.info(f"[COMMAND] SENT | WAYPOINTS({len(waypoints)} items) -> DST: {dst}")
