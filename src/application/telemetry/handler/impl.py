from __future__ import annotations
# src/application/telemetry/handler/impl.py

from src.application.telemetry.tools.cache import set_device_data
from src.shared.log.logger import logger

def gps(data: dict, src_id: int):
    gps = {
        "lat": data["lat"],
        "lon": data["lon"],
        "alt": data["alt"],
    }
    set_device_data(src_id, "gps", gps)
    logger.info(f"[TELEMETRY] GPS received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → LAT: {gps['lat']:.6f}, LON: {gps['lon']:.6f}, ALT: {gps['alt']:.2f}")

def imu(data: dict, src_id: int):
    imu = {
        "roll": data["roll"],
        "pitch": data["pitch"],
        "yaw": data["yaw"],
    }
    set_device_data(src_id, "imu", imu)
    logger.info(f"[TELEMETRY] IMU received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → Roll: {imu['roll']:.2f}, Pitch: {imu['pitch']:.2f}, Yaw: {imu['yaw']:.2f}")

def battery(data: dict, src_id: int):
    battery = {
        "voltage": data["voltage"],
        "current": data["current"],
        "level": data["level"]
    }
    set_device_data(src_id, "battery", battery)
    logger.info(f"[TELEMETRY] BATTERY received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → V: {battery['voltage']:.2f}V, I: {battery['current']:.2f}A, Level: {battery['level']:.1f}%")

def heartbeat(data: dict, src_id: int):
    hb = {
        "mode": data["mode"],
        "health": data["health"],
        "is_armed": data["is_armed"],
        "gps_fix": data["gps_fix"],
        "sat_count": data["sat_count"]
    }
    set_device_data(src_id, "heartbeat", hb)
    logger.info(f"[TELEMETRY] HEARTBEAT received from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] → MODE: {hb['mode']}, HEALTH: {hb['health']}, ARMED: {hb['is_armed']}, GPS_FIX: {hb['gps_fix']}, SATS: {hb['sat_count']}")

def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")