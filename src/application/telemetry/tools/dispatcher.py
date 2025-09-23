from __future__ import annotations
# src/application/telemetry/tools/dispatcher.py

"""
Telemetry Dispatcher Module

Constructs and sends various telemetry frames over a communication interface.
Each function builds a specific telemetry payload (GPS, IMU, Battery, Heartbeat)
and transmits it, while logging the action for traceability.
"""

from src.application.telemetry.tools.builder import (
    build_tlm_gps,
    build_tlm_imu,
    build_tlm_battery,
    build_tlm_heartbeat,
    build_tlm_barometer,
    build_tlm_ping
)
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger

def send_tlm_gps(
    interface,
    lat: float,
    lon: float,
    alt: float,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a GPS telemetry frame containing latitude, longitude, and altitude.

    Args:
        interface: Communication interface instance (UART, UDP, etc.).
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.
        alt (float): Altitude in meters above sea level.
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, omitted.
    """
    frame = build_tlm_gps(lat, lon, alt, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT GPS | DST: {dst} | LAT: {lat:.6f}, LON: {lon:.6f}, ALT: {alt:.2f}"
    )

def send_tlm_imu(
    interface,
    roll: float,
    pitch: float,
    yaw: float,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an IMU telemetry frame containing roll, pitch, and yaw angles.

    Args:
        interface: Communication interface instance.
        roll (float): Roll angle in degrees.
        pitch (float): Pitch angle in degrees.
        yaw (float): Yaw angle in degrees.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_imu(roll, pitch, yaw, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT IMU | DST: {dst} | ROLL: {roll:.2f}, PITCH: {pitch:.2f}, YAW: {yaw:.2f}"
    )

def send_tlm_battery(
    interface,
    voltage: float,
    current: float,
    level: float,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a Battery telemetry frame containing voltage, current draw, and charge level.

    Args:
        interface: Communication interface instance.
        voltage (float): Battery voltage in volts.
        current (float): Current draw in amperes.
        level (float): Remaining battery percentage (0.0–100.0).
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_battery(voltage, current, level, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT BATTERY | DST: {dst} | VOLT: {voltage:.2f} V, CURR: {current:.2f} A, LEVEL: {level:.1f}%"
    )

def send_tlm_heartbeat(
    interface,
    mode: str,
    health: str,
    is_armed: bool,
    gps_fix: bool,
    sat_count: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a Heartbeat telemetry frame conveying system state information.

    Args:
        interface: Communication interface instance.
        mode (str): Flight mode identifier (e.g., "STABILIZE", "GUIDED").
        health (str): Overall system health status (e.g., "OK", "WARN").
        is_armed (bool): Whether the vehicle is armed.
        gps_fix (bool): GPS fix status.
        sat_count (int): Number of satellites in view.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_heartbeat(mode, health, is_armed, gps_fix, sat_count, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT HEARTBEAT | DST: {dst} | MODE: {mode}, HEALTH: {health}, "
        f"ARMED: {is_armed}, GPS_FIX: {gps_fix}, SATS: {sat_count}"
    )

def send_tlm_barometer(
    interface,
    vertical_speed: float,
    ground_speed: float,
    altitude_relative: float,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a Barometer telemetry frame.

    Args:
        interface: Communication interface instance.
        vertical_speed (float): Vertical speed in m/s.
        ground_speed (float): Ground speed of the vehicle in m/s.
        altitude_relative (float): Altitude relative to home in meters.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_barometer(vertical_speed, ground_speed, altitude_relative, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT BAROMETER | DST: {dst} | V_SPEED: {vertical_speed:.2f}, GND_SPEED: {ground_speed:.2f}, ALT_REL: {altitude_relative:.2f}"
    )

# --- State for auto-ping ---
_ping_sequence = 0

def send_tlm_ping(
    interface,
    sequence: int | None = None,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a Ping telemetry frame.

    If sequence is not provided, an auto-incrementing sequence number will be used.

    Args:
        interface: Communication interface instance.
        sequence (int | None, optional): A sequence number for the ping.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    global _ping_sequence
    if sequence is None:
        sequence = _ping_sequence
        _ping_sequence += 1

    frame = build_tlm_ping(sequence, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT PING | DST: {dst} | SEQUENCE: {sequence}"
    )
