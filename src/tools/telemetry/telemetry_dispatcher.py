# /src/tools/telemetry/telemetry_dispatcher.py
from src.tools.telemetry.telemetry_builder import (
    build_tlm_gps,
    build_tlm_imu,
    build_tlm_battery
)
from src.tools.comm.transmitter import send_frame
from src.tools.log.logger import logger


def send_tlm_gps(interface, lat: float, lon: float, alt: float, dst: int = 0xFF, src: int = None):
    frame = build_tlm_gps(lat, lon, alt, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | GPS -> DST: {dst} | LAT: {lat}, LON: {lon}, ALT: {alt}")


def send_tlm_imu(interface, roll: float, pitch: float, yaw: float, dst: int = 0xFF, src: int = None):
    frame = build_tlm_imu(roll, pitch, yaw, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | IMU -> DST: {dst} | ROLL: {roll}, PITCH: {pitch}, YAW: {yaw}")


def send_tlm_battery(interface, voltage: float, current: float, level: float, dst: int = 0xFF, src: int = None):
    frame = build_tlm_battery(voltage, current, level, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | BATTERY -> DST: {dst} | VOLT: {voltage}V, CURR: {current}A, LEVEL: {level}%")
