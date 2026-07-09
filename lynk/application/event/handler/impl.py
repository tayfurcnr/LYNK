from __future__ import annotations
from lynk.shared.log.logger import logger

GREEN_BOLD = "\033[92m\033[1m"
RESET = "\033[0m"
_COMMAND_STATUS_NAMES = {
    0: "UNKNOWN",
    1: "COMPLETED",
    2: "FAILED",
    3: "IN_PROGRESS",
}

def default_handler(event_type: int, event_data: dict, src_id: int, interface=None, event_name: str = ""):
    """Default handler for events without specific implementation."""
    # Dispatcher already logs a standardized colored RECV/PARAMS pair.
    # Keep default handler silent to avoid duplicate event logs.
    return

# Detection Events
def qr_detected(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle QR code detection event."""
    payload = event_data.get("payload", {})
    qr_code = payload.get("qr_code", "")
    confidence = payload.get("confidence", 0.0)
    logger.info(f"[EVENT] QR Detected: '{qr_code}' (confidence: {confidence:.2f}) from vehicle {src_id}")

def obstacle_detected(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle obstacle detection event."""
    payload = event_data.get("payload", {})
    distance = payload.get("distance_m", 0.0)
    bearing = payload.get("bearing_deg", 0.0)
    logger.info(f"[EVENT] Obstacle detected: {distance:.1f}m at {bearing:.0f}° from vehicle {src_id}")

# Safety Events
def collision_risk(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle collision risk event."""
    payload = event_data.get("payload", {})
    target_id = payload.get("target_vehicle_id", 0)
    distance = payload.get("distance_m", 0.0)
    ttc = payload.get("time_to_collision_s", 0.0)
    logger.warning(f"[EVENT] COLLISION RISK: Vehicle {src_id} -> Vehicle {target_id}, distance: {distance:.1f}m, TTC: {ttc:.1f}s")

def battery_low(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle low battery event."""
    payload = event_data.get("payload", {})
    voltage = payload.get("voltage", 0.0)
    percent = payload.get("remaining_percent", 0)
    logger.warning(f"[EVENT] Battery low on vehicle {src_id}: {percent}% ({voltage:.2f}V)")

def failsafe_triggered(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle failsafe triggered event."""
    payload = event_data.get("payload", {})
    reason = payload.get("reason", 0)
    action = payload.get("action", 0)
    logger.warning(f"[EVENT] Failsafe triggered on vehicle {src_id}: reason={reason}, action={action}")

def emergency_crash(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle emergency crash event."""
    payload = event_data.get("payload", {})
    reason = payload.get("reason", 0)
    altitude = payload.get("altitude_m", 0.0)
    logger.critical(f"[EVENT] EMERGENCY CRASH: Vehicle {src_id} crashed at {altitude:.1f}m, reason={reason}")

# System Events
def gps_degraded(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle GPS degraded event."""
    payload = event_data.get("payload", {})
    satellites = payload.get("satellites", 0)
    hdop = payload.get("hdop", 0.0)
    logger.warning(f"[EVENT] GPS degraded on vehicle {src_id}: {satellites} sats, HDOP: {hdop:.1f}")

def link_quality_degraded(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle link quality degraded event."""
    payload = event_data.get("payload", {})
    quality = payload.get("link_quality_percent", 0)
    logger.warning(f"[EVENT] Link quality degraded on vehicle {src_id}: {quality}%")

def motor_failure(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle motor failure event."""
    payload = event_data.get("payload", {})
    motor_id = payload.get("motor_id", 0)
    failure_type = payload.get("failure_type", 0)
    logger.critical(f"[EVENT] MOTOR FAILURE: Vehicle {src_id}, motor {motor_id}, type={failure_type}")

def command_status(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle command status event."""
    payload = event_data.get("payload", {})
    command_name = payload.get("command_name", "")
    command_tx_id = payload.get("command_tx_id", "")
    raw_status = payload.get("status", 0)
    error_code = payload.get("error_code", 0)
    error_message = payload.get("error_message", "")
    try:
        status_val = int(raw_status)
    except Exception:
        status_val = 0
    status_name = _COMMAND_STATUS_NAMES.get(status_val, "UNKNOWN")
    logger.info(
        f"[EVENT] COMMAND_STATUS: {command_name} tx={command_tx_id} status={status_name}-[{status_val}] "
        f"error_code={error_code} error_message='{error_message}' src={src_id}"
    )

# Mission Events
def mission_waypoint_reached(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle mission waypoint reached event."""
    payload = event_data.get("payload", {})
    wp_index = payload.get("waypoint_index", 0)
    total = payload.get("total_waypoints", 0)
    logger.info(f"[EVENT] Vehicle {src_id} reached waypoint {wp_index}/{total}")

def mission_complete(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle mission complete event."""
    payload = event_data.get("payload", {})
    total_wp = payload.get("total_waypoints", 0)
    distance = payload.get("total_distance_m", 0.0)
    logger.info(f"[EVENT] Vehicle {src_id} completed mission: {total_wp} waypoints, {distance:.1f}m")

# Swarm Events
def formation_broken(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle formation broken event."""
    payload = event_data.get("payload", {})
    missing_id = payload.get("missing_vehicle_id", 0)
    logger.warning(f"[EVENT] Formation broken: Vehicle {missing_id} missing (reported by {src_id})")

def vehicle_lost(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle vehicle lost event."""
    payload = event_data.get("payload", {})
    lost_id = payload.get("lost_vehicle_id", 0)
    logger.warning(f"[EVENT] Vehicle {lost_id} lost (reported by {src_id})")

def crash_detected(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle crash detected event."""
    payload = event_data.get("payload", {})
    crashed_id = payload.get("crashed_vehicle_id", 0)
    logger.critical(f"[EVENT] CRASH DETECTED: Vehicle {crashed_id} (reported by {src_id})")

def target_detected(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle target detected event."""
    payload = event_data.get("payload", {})
    latitude = payload.get("latitude", 0.0)
    longitude = payload.get("longitude", 0.0)
    altitude_m = payload.get("altitude_m", 0.0)
    detected_at = payload.get("detected_at", "")
    detected_at_unix_ms = payload.get("detected_at_unix_ms", 0)
    logger.info(
        "[EVENT] TARGET DETECTED: "
        f"lat={latitude:.6f}, lon={longitude:.6f}, alt={altitude_m:.1f}m, "
        f"detected_at='{detected_at}', ts_ms={detected_at_unix_ms} (reported by {src_id})"
    )

def custom_event(event_type: int, event_data: dict, src_id: int, interface=None):
    """Handle custom event."""
    return
