from __future__ import annotations
# src/application/telemetry/handler/impl.py

from src.application.telemetry.tools.cache import set_device_data
from src.shared.log.logger import logger

def default_handler(data: dict, src_id: int, tlm_name: str, team_id: Optional[int] = None, hop_count: int = 0):
    """
    Default telemetry handler for types without custom implementation.
    
    Automatically logs and caches telemetry data.
    
    Args:
        data (dict): Telemetry data dictionary.
        src_id (int): Source device ID.
        tlm_name (str): Telemetry type name (e.g., "COMPASS").
        team_id (int, optional): Source team ID.
        hop_count (int, optional): Number of hops.
    """
    set_device_data(src_id, tlm_name.lower(), data, team_id=team_id, hop_count=hop_count)
    
    # Format data for logging
    param_str = ", ".join(f"{k}={v}" for k, v in data.items())
    logger.debug(f"[TELEMETRY] {tlm_name} received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → {param_str}")


def gps(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    gps_data = {
        "lat": data["lat"],
        "lon": data["lon"],
        "alt": data["alt"],
    }
    set_device_data(src_id, "gps", gps_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] GPS received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → LAT: {gps_data['lat']:.6f}, LON: {gps_data['lon']:.6f}, ALT: {gps_data['alt']:.2f}")

def imu(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    imu_data = {
        "roll": data["roll"],
        "pitch": data["pitch"],
        "yaw": data["yaw"],
    }
    set_device_data(src_id, "imu", imu_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] IMU received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → Roll: {imu_data['roll']:.2f}, Pitch: {imu_data['pitch']:.2f}, Yaw: {imu_data['yaw']:.2f}")

def battery(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    battery_data = {
        "voltage": data["voltage"],
        "current": data["current"],
        "level": data["level"]
    }
    set_device_data(src_id, "battery", battery_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] BATTERY received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → V: {battery_data['voltage']:.2f}V, I: {battery_data['current']:.2f}A, Level: {battery_data['level']:.1f}%")

def heartbeat(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    hb = {
        "mode": data["mode"],
        "health": data["health"],
        "is_armed": data["is_armed"],
        "gps_fix": data["gps_fix"],
        "sat_count": data["sat_count"]
    }
    set_device_data(src_id, "heartbeat", hb, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] HEARTBEAT received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → MODE: {hb['mode']}, HEALTH: {hb['health']}, ARMED: {hb['is_armed']}, GPS_FIX: {hb['gps_fix']}, SATS: {hb['sat_count']}")

def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")

def barometer(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    baro_data = {
        "vertical_speed": data["vertical_speed"],
        "ground_speed": data["ground_speed"],
        "altitude_relative": data["altitude_relative"],
    }
    set_device_data(src_id, "barometer", baro_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] Barometer received from SRC: {src_id} (Team: {team_id})")
    logger.debug(f"[TELEMETRY] → Vertical Speed: {baro_data['vertical_speed']:.2f}, Ground Speed: {baro_data['ground_speed']:.2f}, Altitude Relative: {baro_data['altitude_relative']:.2f}")

def ping(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    sequence = data["sequence"]
    set_device_data(src_id, "ping", {"sequence": sequence}, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] PING received from SRC: {src_id} (Team: {team_id}) with sequence {sequence}")
