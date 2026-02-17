from __future__ import annotations
# lynk/application/telemetry/handler/impl.py

from lynk.application.telemetry.tools.cache import set_device_data
from lynk.shared.log.logger import logger

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
        "alt_m": data["alt_m"],
        "fix_type": data["fix_type"],
        "sat_count": data["sat_count"],
        "hdop": data["hdop"],
        "timestamp_ms": data["timestamp_ms"],
        "rel_alt_m": data["rel_alt_m"],
    }
    set_device_data(src_id, "gps", gps_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] GPS received from SRC: {src_id} (Team: {team_id})")
    logger.debug(
        f"[TELEMETRY] → LAT: {gps_data['lat']:.7f}, LON: {gps_data['lon']:.7f}, "
        f"ALT: {gps_data['alt_m']:.2f}m, REL: {gps_data['rel_alt_m']:.2f}m, "
        f"FIX: {gps_data['fix_type']}, SATS: {gps_data['sat_count']}, HDOP: {gps_data['hdop']:.2f}"
    )


def attitude(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    attitude_data = {
        "roll_deg": data["roll_deg"],
        "pitch_deg": data["pitch_deg"],
        "yaw_deg": data["yaw_deg"],
        "timestamp_ms": data["timestamp_ms"],
    }
    set_device_data(src_id, "attitude", attitude_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] ATTITUDE received from SRC: {src_id} (Team: {team_id})")
    logger.debug(
        f"[TELEMETRY] → Roll: {attitude_data['roll_deg']:.2f}°, "
        f"Pitch: {attitude_data['pitch_deg']:.2f}°, Yaw: {attitude_data['yaw_deg']:.2f}°"
    )

def battery(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    battery_data = {
        "voltage_v": data["voltage_v"],
        "current_a": data["current_a"],
        "level_pct": data["level_pct"],
        "timestamp_ms": data["timestamp_ms"],
    }
    set_device_data(src_id, "battery", battery_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] BATTERY received from SRC: {src_id} (Team: {team_id})")
    logger.debug(
        f"[TELEMETRY] → V: {battery_data['voltage_v']:.2f}V, "
        f"I: {battery_data['current_a']:.2f}A, Level: {battery_data['level_pct']:.1f}%"
    )

def state(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    state_data = {
        "mode": data["mode"],
        "is_armed": data["is_armed"],
        "connected": data["connected"],
        "timestamp_ms": data["timestamp_ms"],
    }
    set_device_data(src_id, "state", state_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] STATE received from SRC: {src_id} (Team: {team_id})")
    logger.debug(
        f"[TELEMETRY] → MODE: {state_data['mode']}, ARMED: {state_data['is_armed']}, "
        f"CONNECTED: {state_data['connected']}"
    )


def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")

def vfr_hud(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    vfr_data = {
        "airspeed_ms": data["airspeed_ms"],
        "groundspeed_ms": data["groundspeed_ms"],
        "heading_deg": data["heading_deg"],
        "throttle": data["throttle"],
        "alt_m": data["alt_m"],
        "climb_ms": data["climb_ms"],
        "timestamp_ms": data["timestamp_ms"],
    }
    set_device_data(src_id, "vfr_hud", vfr_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] VFR_HUD received from SRC: {src_id} (Team: {team_id})")
    logger.debug(
        f"[TELEMETRY] → GS: {vfr_data['groundspeed_ms']:.2f}m/s, "
        f"HDG: {vfr_data['heading_deg']:.1f}°, ALT: {vfr_data['alt_m']:.2f}m"
    )

def heartbeat(data: dict, src_id: int, team_id: Optional[int] = None, hop_count: int = 0):
    sequence = data["sequence"]
    ts = data["timestamp_ms"]
    hb_data = {"sequence": sequence, "timestamp_ms": ts}
    set_device_data(src_id, "heartbeat", hb_data, team_id=team_id, hop_count=hop_count)
    logger.debug(f"[TELEMETRY] HEARTBEAT received from SRC: {src_id} (Team: {team_id}) | SEQ: {sequence}")
