# /src/tools/telemetry/telemetry_dispatcher.py
from src.tools.telemetry.telemetry_builder import (
    build_tlm_gps,
    build_tlm_imu,
    build_tlm_battery,
    build_tlm_heartbeat
)
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger


def send_tlm_gps(interface,
    lat: float,
    lon: float,
    alt: float,
    dst: int = 0xFF,
    src: int = None
):
    """
    Sends a GPS telemetry frame (latitude, longitude, altitude).

    Parameters:
        interface: Communication interface (UART, UDP, etc.)
        lat (float): Latitude in degrees
        lon (float): Longitude in degrees
        alt (float): Altitude in meters
        dst (int): Destination device ID (default: 0xFF = broadcast)
        src (int): Source device ID (optional)
    """
    frame = build_tlm_gps(lat, lon, alt, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | GPS -> DST: {dst} | LAT: {lat}, LON: {lon}, ALT: {alt}")


def send_tlm_imu(
    interface,
    roll: float,
    pitch: float,
    yaw: float,
    dst: int = 0xFF,
    src: int = None
):
    """
    Sends an IMU telemetry frame (roll, pitch, yaw).

    Parameters:
        interface: Communication interface
        roll (float): Roll angle in degrees
        pitch (float): Pitch angle in degrees
        yaw (float): Yaw angle in degrees
        dst (int): Destination device ID
        src (int): Source device ID
    """
    frame = build_tlm_imu(roll, pitch, yaw, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | IMU -> DST: {dst} | ROLL: {roll}, PITCH: {pitch}, YAW: {yaw}")


def send_tlm_battery(
    interface,
    voltage: float,
    current: float,
    level: float,
    dst: int = 0xFF,
    src: int = None
):
    """
    Sends a BATTERY telemetry frame (voltage, current, battery level).

    Parameters:
        interface: Communication interface
        voltage (float): Battery voltage in volts
        current (float): Current draw in amperes
        level (float): Remaining battery percentage (0–100)
        dst (int): Destination device ID
        src (int): Source device ID
    """
    frame = build_tlm_battery(voltage, current, level, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | BATTERY -> DST: {dst} | VOLT: {voltage}V, CURR: {current}A, LEVEL: {level}%")

def send_tlm_heartbeat(
    interface,
    mode: str,
    health: str,
    is_armed: bool,
    gps_fix: bool,
    sat_count: int,
    dst: int = 0xFF,
    src: int = None
):
    """
    Sends a HEARTBEAT telemetry frame to the target node.

    Parameters:
        interface: The communication interface to send the frame
        mode (str): Flight mode (e.g., "GUIDED")
        health (str): System health status (e.g., "OK")
        is_armed (bool): Armed state
        gps_fix (bool): GPS fix state
        sat_count (int): Number of satellites
        dst (int): Destination ID
        src (int): Source ID
    """
    frame = build_tlm_heartbeat(mode, health, is_armed, gps_fix, sat_count, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | HEARTBEAT -> DST: {dst} | MODE: {mode}, HEALTH: {health}, ARMED: {is_armed}, FIX: {gps_fix}, SATS: {sat_count}")
