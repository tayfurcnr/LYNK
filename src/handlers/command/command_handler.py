# src/handlers/command_handler.py

from src.tools.log.logger import logger
from src.serializers.command_serializer import deserialize_command
from src.tools.command.ack_dispatcher import send_ack
import struct
from collections import namedtuple

# === INDIVIDUAL COMMAND HANDLERS ===

def handle_reboot(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] SENT | CMD: REBOOT")
    send_ack(interface, cmd_id, src_id, True, 0)

def handle_set_mode(cmd_id, params, src_id, interface):
    if params:
        mode = params[0]
        logger.info(f"[COMMAND] SENT | CMD: SET_MODE | MODE: {mode}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SET_MODE")
        send_ack(interface, cmd_id, src_id, False, 1)

def handle_takeoff(cmd_id, params, src_id, interface):
    if len(params) == 4:
        alt = struct.unpack(">f", params)[0]
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m")
        send_ack(interface, cmd_id, src_id, True, 0)
    elif len(params) == 16:
        alt, lat, lon, target_alt = struct.unpack(">ffff", params)
        logger.info(f"[COMMAND] SENT | CMD: TAKEOFF | ALT: {alt:.2f} m | TARGET: {lat:.6f}, {lon:.6f}, {target_alt:.2f} m")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: TAKEOFF | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 1)

def handle_landing(cmd_id, params, src_id, interface):
    if len(params) == 0:
        logger.info("[COMMAND] SENT | CMD: LANDING | MODE: LOCAL")
        send_ack(interface, cmd_id, src_id, True, 0)
    elif len(params) == 8:
        lat, lon = struct.unpack(">ff", params)
        logger.info(f"[COMMAND] SENT | CMD: LANDING | TARGET: LAT={lat:.6f}, LON={lon:.6f}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: LANDING | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 1)

def handle_gimbal(cmd_id, params, src_id, interface):
    if len(params) == 12:
        yaw, pitch, roll = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GIMBAL_CTRL | YAW: {yaw}, PITCH: {pitch}, ROLL: {roll}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GIMBAL_CTRL | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 1)

def handle_goto(cmd_id, params, src_id, interface):
    if len(params) == 12:
        lat, lon, alt = struct.unpack(">fff", params)
        logger.info(f"[COMMAND] SENT | CMD: GOTO | TARGET: LAT={lat}, LON={lon}, ALT={alt}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GOTO | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 2)

def handle_follow_me(cmd_id, params, src_id, interface):
    if len(params) == 8:
        target_id, alt = struct.unpack(">if", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id} | ALT: {alt}")
        send_ack(interface, cmd_id, src_id, True, 0)
    elif len(params) == 4:
        target_id, = struct.unpack(">i", params)
        logger.info(f"[COMMAND] SENT | CMD: FOLLOW_ME | TARGET: {target_id}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FOLLOW_ME | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 1)

def handle_waypoints(cmd_id, params, src_id, interface):
    if len(params) >= 12:
        waypoints = []
        for i in range(0, len(params), 12):
            lat, lon, alt = struct.unpack(">fff", params[i:i+12])
            waypoints.append((lat, lon, alt))
        logger.info(f"[COMMAND] SENT | CMD: WAYPOINTS | COUNT: {len(waypoints)} | DATA: {waypoints}")
        send_ack(interface, cmd_id, src_id, True, 0)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: WAYPOINTS | PRM LEN: {len(params)}")
        send_ack(interface, cmd_id, src_id, False, 2)

def handle_unknown(cmd_id, params, src_id, interface):
    logger.warning(f"[COMMAND] UNKNOWN CMD: {cmd_id} FROM SRC: {src_id}")
    send_ack(interface, cmd_id, src_id, False, 2)

# === COMMAND DEFINITIONS ===

CommandDefinition = namedtuple("CommandDefinition", ["name", "handler"])

command_definitions = {
    0x01: CommandDefinition("REBOOT",      handle_reboot),
    0x02: CommandDefinition("SET_MODE",    handle_set_mode),
    0x03: CommandDefinition("TAKEOFF",     handle_takeoff),
    0x04: CommandDefinition("LANDING",     handle_landing),
    0x05: CommandDefinition("GIMBAL_CTRL", handle_gimbal),
    0x06: CommandDefinition("GOTO",        handle_goto),
    0x07: CommandDefinition("FOLLOW_ME",   handle_follow_me),
    0x09: CommandDefinition("WAYPOINTS",   handle_waypoints),
}

# === MAIN COMMAND HANDLER ===

def handle_command(payload: bytes, frame_meta: dict, interface):
    try:
        cmd = deserialize_command(payload)
        cmd_id = cmd["command_id"]
        params = cmd["params"]
        src_id = frame_meta["src_id"]

        cmd_def = command_definitions.get(cmd_id, CommandDefinition("UNKNOWN", handle_unknown))
        logger.info(f"[COMMAND] RECEIVED | CMD: {cmd_id} ({cmd_def.name}) FROM SRC: {src_id} | PRM: {params}")
        cmd_def.handler(cmd_id, params, src_id, interface)

    except Exception as e:
        logger.error(f"[COMMAND] ERROR | Exception during parsing: {e}")
