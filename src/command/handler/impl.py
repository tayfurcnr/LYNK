# src/handlers/command_handler.py

from src.tools.log.logger import logger
from src.tools.ack.ack_dispatcher import send_ack
from src.tools.ack.status_codes import STATUS_SUCCESS, STATUS_INVALID_PARAMS, STATUS_UNKNOWN_COMMAND
import struct

# === INDIVIDUAL COMMAND HANDLERS ===

def reboot(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] SENT | CMD: REBOOT")
    send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)

def set_mode(cmd_id, params, src_id, interface):
    if params:
        mode = params[0]
        logger.info(f"[COMMAND] SENT | CMD: SET_MODE | MODE: {mode}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SET_MODE")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def takeoff(cmd_id, params, src_id, interface):
    if len(params) == 4:
        alt = struct.unpack(">f", params)[0]
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    elif len(params) == 16:
        alt, lat, lon, target_alt = struct.unpack(">ffff", params)
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m | TARGET: {lat:.6f}, {lon:.6f}, {target_alt:.2f} m")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: TAKEOFF | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def landing(cmd_id, params, src_id, interface):
    if len(params) == 0:
        logger.info("[COMMAND] SENT | CMD: LANDING | MODE: LOCAL")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    elif len(params) == 8:
        lat, lon = struct.unpack(">ff", params)
        logger.info(f"[COMMAND] SENT | CMD: LANDING | TARGET: LAT={lat:.6f}, LON={lon:.6f}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: LANDING | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def gimbal(cmd_id, params, src_id, interface):
    if len(params) == 12:
        yaw, pitch, roll = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GIMBAL_CTRL | YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GIMBAL_CTRL | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def goto(cmd_id, params, src_id, interface):
    if len(params) == 12:
        lat, lon, alt = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GOTO | TARGET: LAT={lat}, LON={lon}, ALT={alt}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GOTO | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def follow_me(cmd_id, params, src_id, interface):
    if len(params) == 8:
        target_id, alt = struct.unpack(">if", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id} | ALT: {alt}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    elif len(params) == 4:
        target_id, = struct.unpack(">i", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FOLLOW_ME | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)

def waypoints(cmd_id, params, src_id, interface):
    if len(params) >= 12:
        waypoints = []
        for i in range(0, len(params), 12):
            lat, lon, alt = struct.unpack(">fff", params[i:i+12])
            waypoints.append((lat, lon, alt))
        logger.info(f"[COMMAND] SENT | CMD: WAYPOINTS | COUNT: {len(waypoints)} | DATA: {waypoints}")
        send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: WAYPOINTS | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, STATUS_INVALID_PARAMS)