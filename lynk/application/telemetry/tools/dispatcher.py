from __future__ import annotations
# lynk/application/telemetry/tools/dispatcher.py
import logging
from typing import Optional
import time

"""
Telemetry Dispatcher Module

Constructs and sends various telemetry frames over a communication interface.
Each function builds a specific telemetry payload (GPS, Attitude, Battery, State, VfrHud)
and transmits it, while logging the action for traceability.
"""

import lynk.core.frame_codec as codec
from lynk.application.telemetry.tools.builder import (
    build_tlm_gps,
    build_tlm_attitude,
    build_tlm_battery,
    build_tlm_state,
    build_tlm_vfr_hud,
    build_tlm_heartbeat
)
from lynk.shared.comm.transmitter import send_frame
from lynk.shared.log.logger import logger
from typing import Dict, List, Any

# Map for dynamic telemetry callbacks: tlm_id -> list of functions
_tlm_handlers: Dict[int, List[Any]] = {}

def register_handler(tlm_id: int, callback: Any) -> None:
    """
    Register a dynamic callback for a specific telemetry type.
    
    Args:
        tlm_id (int): Telemetry ID (e.g., 4 for STATE, 1 for GPS)
        callback (callable): Function taking tlm_data (dict) and metadata
    """
    if tlm_id not in _tlm_handlers:
        _tlm_handlers[tlm_id] = []
    _tlm_handlers[tlm_id].append(callback)
    logger.debug(f"[TELEMETRY] Callback registered for ID: {tlm_id}")

def _get_dynamic_handlers(tlm_id: int) -> List[Any]:
    """Retrieve registered handlers for a specific telemetry ID."""
    return _tlm_handlers.get(tlm_id, [])

def send_telemetry(
    interface,
    name: str,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    **params
) -> None:
    """
    Generic telemetry sender using Protobuf introspection.
    
    Automatically handles any telemetry type defined in the Protobuf schema.
    
    Args:
        interface: Communication interface instance.
        name (str): Telemetry name (e.g., "GPS", "IMU", "COMPASS").
        dst (int): Destination device ID (default: 0xFF for broadcast).
        src (int | None): Source device ID; if None, loaded from config.
        dst_team_id (int | None): Destination team ID for team filtering.
        **params: Telemetry parameters as keyword arguments.
    
    Example:
        send_telemetry(interface, "GPS", lat=37.0, lon=35.0, alt_m=100.0, fix_type=3, sat_count=12, hdop=1.0, timestamp_ms=0)
        send_telemetry(interface, "COMPASS", heading=45.2, declination=1.3, dst=1)
    """
    from lynk.application.telemetry.serializer.dispatcher import _get_tlm_fields
    from lynk.application.telemetry.tools.builder import build_tlm_frame
    
    # Get telemetry schema from Protobuf introspection
    tlm_fields = _get_tlm_fields()
    name_upper = name.upper()
    
    if name_upper not in tlm_fields:
        raise ValueError(f"Unknown telemetry type: {name}. Available: {list(tlm_fields.keys())}")
    
    field_name, param_list, tlm_id = tlm_fields[name_upper]
    
    # Validate parameters
    missing = [p for p in param_list if p not in params]
    if missing:
        raise ValueError(f"{name} missing required parameters: {missing}")
    
    # Order parameters according to Protobuf schema
    ordered_params = [params[p] for p in param_list]
    
    # Build and send frame
    frame = build_tlm_frame(name_upper, ordered_params, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    
    # Log with parameter summary
    param_str = ", ".join(f"{k}={v}" for k, v in params.items())
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.debug(f"[TELEMETRY] SENT {name_upper} | {target} | {param_str}")


def send_tlm_gps(
    interface,
    lat: float,
    lon: float,
    alt_m: float,
    rel_alt_m: float = 0.0,
    fix_type: int = 3,
    sat_count: int = 0,
    hdop: float = 1.0,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a GPS telemetry frame containing position, fix quality, and timing.

    Args:
        interface: Communication interface instance (UART, UDP, etc.).
        lat (float): Latitude in decimal degrees (double precision).
        lon (float): Longitude in decimal degrees (double precision).
        alt_m (float): Altitude in meters above sea level.
        rel_alt_m (float): Relative altitude above home in meters.
        fix_type (int): MAVLink GPS_FIX_TYPE (0-8).
        sat_count (int): Number of satellites in view.
        hdop (float): HDOP value.
        timestamp_ms (int): Unix epoch time in ms.
        dst (int, optional): Destination device ID (default: 0xFF for broadcast).
        src (int | None, optional): Source device ID; if None, omitted.
    """
    frame = build_tlm_gps(
        lat, lon, alt_m, rel_alt_m, fix_type, sat_count, hdop, timestamp_ms,
        dst, src, team_id=dst_team_id
    )
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.debug(
        f"[TELEMETRY] SENT GPS | {target} | "
        f"LAT: {lat:.7f}, LON: {lon:.7f}, ALT: {alt_m:.2f}m, REL: {rel_alt_m:.2f}m, "
        f"FIX: {fix_type}, SATS: {sat_count}, HDOP: {hdop:.2f}"
    )

def send_tlm_attitude(
    interface,
    roll_deg: float,
    pitch_deg: float,
    yaw_deg: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an Attitude telemetry frame containing roll, pitch, and yaw angles.

    Args:
        interface: Communication interface instance.
        roll_deg (float): Roll angle in degrees.
        pitch_deg (float): Pitch angle in degrees.
        yaw_deg (float): Yaw angle in degrees.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_attitude(roll_deg, pitch_deg, yaw_deg, timestamp_ms, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT ATTITUDE | DST: {dst} | ROLL: {roll_deg:.2f}°, PITCH: {pitch_deg:.2f}°, YAW: {yaw_deg:.2f}°"
    )

def send_tlm_battery(
    interface,
    voltage_v: float,
    current_a: float,
    level_pct: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a Battery telemetry frame containing voltage, current draw, and charge level.

    Args:
        interface: Communication interface instance.
        voltage_v (float): Battery voltage in volts.
        current_a (float): Current draw in amperes.
        level_pct (float): Remaining battery percentage (0.0–100.0).
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_battery(voltage_v, current_a, level_pct, timestamp_ms, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT BATTERY | DST: {dst} | VOLT: {voltage_v:.2f}V, "
        f"CURR: {current_a:.2f}A, LEVEL: {level_pct:.1f}%"
    )

def send_tlm_state(
    interface,
    mode: str,
    is_armed: bool,
    connected: bool = True,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a State telemetry frame conveying vehicle status (MAVROS-aligned).

    Args:
        interface: Communication interface instance.
        mode (str): Flight mode identifier (e.g., "STABILIZE", "GUIDED").
        is_armed (bool): Whether the vehicle is armed.
        connected (bool): FCU connection status (default: True).
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_state(mode, is_armed, connected, timestamp_ms, dst, src)
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT STATE | DST: {dst} | MODE: {mode}, "
        f"ARMED: {is_armed}, CONNECTED: {connected}"
    )

def send_tlm_vfr_hud(
    interface,
    airspeed_ms: float,
    groundspeed_ms: float,
    heading_deg: float,
    throttle: float,
    alt_m: float,
    climb_ms: float,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a VFR_HUD telemetry frame.

    Args:
        interface: Communication interface instance.
        airspeed_ms (float): Airspeed in m/s.
        groundspeed_ms (float): Ground speed in m/s.
        heading_deg (float): Heading in degrees (0-360).
        throttle (float): Throttle percentage (0.0-1.0).
        alt_m (float): Altitude in meters (MSL).
        climb_ms (float): Climb rate in m/s.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
    """
    frame = build_tlm_vfr_hud(
        airspeed_ms, groundspeed_ms, heading_deg, throttle, alt_m, climb_ms, timestamp_ms,
        dst, src
    )
    send_frame(interface, frame)
    logger.debug(
        f"[TELEMETRY] SENT VFR_HUD | DST: {dst} | GS: {groundspeed_ms:.2f}m/s, "
        f"HDG: {heading_deg:.1f}°, ALT: {alt_m:.2f}m"
    )

# --- State for auto-heartbeat ---
_hb_sequence = 0

def send_tlm_heartbeat(
    interface,
    sequence: int | None = None,
    timestamp_ms: int = 0,
    dst: int = 0xFF,
    src: int | None = None,
    dst_team_id: Optional[int] = None
) -> None:
    """
    Send a Heartbeat telemetry frame.

    If sequence is not provided, an auto-incrementing sequence number will be used.

    Args:
        interface: Communication interface instance.
        sequence (int | None, optional): A sequence number for the heartbeat.
        timestamp_ms (int): Unix epoch timestamp in milliseconds.
        dst (int, optional): Destination device ID.
        src (int | None, optional): Source device ID.
        dst_team_id (int | None, optional): Destination team ID.
    """
    global _hb_sequence
    if sequence is None:
        sequence = _hb_sequence
        _hb_sequence += 1
    
    if timestamp_ms == 0:
        timestamp_ms = int(time.time() * 1000)

    frame = build_tlm_heartbeat(sequence, timestamp_ms, dst, src, team_id=dst_team_id)
    send_frame(interface, frame)
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    logger.debug(f"[TELEMETRY] SENT HEARTBEAT | {target} | SEQ: {sequence} | MS: {timestamp_ms}")
