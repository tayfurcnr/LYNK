# src/handlers/command_handler.py

from src.shared.log.logger import logger
from src.application.ack.tools.dispatcher import send_ack_ok, send_ack_error, send_ack_invalid_cmd
import struct

# === INDIVIDUAL COMMAND HANDLERS ===

def reboot(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] SENT | CMD: REBOOT")
    send_ack_ok(interface, "Command executed successfully", dst=src_id)

def set_mode(cmd_id, params, src_id, interface):
    if params:
        mode = params[0]
        logger.info(f"[COMMAND] SENT | CMD: SET_MODE | MODE: {mode}")
        send_ack_ok(interface, f"Mode set to {mode}", dst=src_id)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SET_MODE")
        send_ack_invalid_cmd(interface, "Missing mode parameter for SET_MODE", dst=src_id)

def takeoff(cmd_id, params, src_id, interface):
    if len(params) == 4:
        alt = struct.unpack(">f", params)[0]
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m")
        send_ack_ok(interface, f"Takeoff initiated to {alt:.2f}m", dst=src_id)
    elif len(params) == 16:
        alt, lat, lon, target_alt = struct.unpack(">ffff", params)
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m | TARGET: {lat:.6f}, {lon:.6f}, {target_alt:.2f} m")
        send_ack_ok(interface, f"Takeoff initiated to {alt:.2f}m, target {lat:.6f}, {lon:.6f}, {target_alt:.2f}m", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: TAKEOFF | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for TAKEOFF. Expected 4 or 16 bytes, got {len(params)}", dst=src_id)

def landing(cmd_id, params, src_id, interface):
    if len(params) == 0:
        logger.info("[COMMAND] SENT | CMD: LANDING | MODE: LOCAL")
        send_ack_ok(interface, "Landing initiated (local)", dst=src_id)
    elif len(params) == 8:
        lat, lon = struct.unpack(">ff", params)
        logger.info(f"[COMMAND] SENT | CMD: LANDING | TARGET: LAT={lat:.6f}, LON={lon:.6f}")
        send_ack_ok(interface, f"Landing initiated to target {lat:.6f}, {lon:.6f}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: LANDING | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for LANDING. Expected 0 or 8 bytes, got {len(params)}", dst=src_id)

def gimbal(cmd_id, params, src_id, interface):
    if len(params) == 12:
        yaw, pitch, roll = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GIMBAL_CTRL | YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}")
        send_ack_ok(interface, f"Gimbal control set to YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GIMBAL_CTRL | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for GIMBAL_CTRL. Expected 12 bytes, got {len(params)}", dst=src_id)

def goto(cmd_id, params, src_id, interface):
    if len(params) == 12:
        lat, lon, alt = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GOTO | TARGET: LAT={lat}, LON={lon}, ALT={alt}")
        send_ack_ok(interface, f"GoTo command issued to LAT={lat}, LON={lon}, ALT={alt}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GOTO | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for GOTO. Expected 12 bytes, got {len(params)}", dst=src_id)

def follow_me(cmd_id, params, src_id, interface):
    if len(params) == 8:
        target_id, alt = struct.unpack(">if", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id} | ALT: {alt}")
        send_ack_ok(interface, f"Follow Me command issued for target {target_id} at ALT: {alt}", dst=src_id)
    elif len(params) == 4:
        target_id, = struct.unpack(">i", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id}")
        send_ack_ok(interface, f"Follow Me command issued for target {target_id}", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FOLLOW_ME | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for FOLLOW_ME. Expected 4 or 8 bytes, got {len(params)}", dst=src_id)

def waypoints(cmd_id, params, src_id, interface):
    if len(params) >= 12:
        waypoints = []
        for i in range(0, len(params), 12):
            lat, lon, alt = struct.unpack(">fff", params[i:i+12])
            waypoints.append((lat, lon, alt))
        logger.info(f"[COMMAND] SENT | CMD: WAYPOINTS | COUNT: {len(waypoints)} | DATA: {waypoints}")
        send_ack_ok(interface, f"Waypoints command issued with {len(waypoints)} waypoints", dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: WAYPOINTS | PRM LEN: {len(params)}")
        send_ack_invalid_cmd(interface, f"Invalid parameters for WAYPOINTS. Expected multiple of 12 bytes, got {len(params)}", dst=src_id)