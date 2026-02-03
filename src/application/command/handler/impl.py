from __future__ import annotations
# src/handlers/command_handler.py

from src.shared.log.logger import logger
from src.application.ack.tools.dispatcher import send_ack_ok, send_ack_error, send_ack_invalid_cmd
from src.application.command.tools.cache import set_last_command
import struct
import json

# === INDIVIDUAL COMMAND HANDLERS ===

def system_reboot(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] RECV | CMD: SYSTEM_REBOOT")
    set_last_command(cmd_id, params, {})
    # send_ack_ok(interface, cmd_id, dst=src_id)

def system_set_vehicle_id(cmd_id, params, src_id, interface):
    if len(params) == 4:
        vehicle_id, = struct.unpack(">I", params)
        from src.shared.config.manager import get_config, save_config
        get_config()["vehicle"]["id"] = vehicle_id
        parsed = {"id": vehicle_id}
        logger.info(f"[COMMAND] RECV | CMD: SYSTEM_SET_VEHICLE_ID | ID updated to: {vehicle_id}")
        save_config() # Persistent save
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_VEHICLE_ID | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def system_set_team_id(cmd_id, params, src_id, interface):
    if len(params) == 1:
        team_id, = struct.unpack(">B", params)
        from src.shared.config.manager import get_config, save_config
        get_config()["vehicle"]["team_id"] = team_id
        parsed = {"team_id": team_id}
        logger.info(f"[COMMAND] RECV | CMD: SYSTEM_SET_TEAM_ID | Team ID updated to: {team_id}")
        save_config() # Persistent save
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_TEAM_ID | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_mode(cmd_id, params, src_id, interface):
    if params:
        try:
            mode = params.decode('utf-8')
            parsed = {"mode": mode}
            logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_MODE | MODE: {mode}")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_MODE | Could not decode mode string")
            # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_MODE")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_arming(cmd_id, params, src_id, interface):
    if len(params) == 1:
        arm, = struct.unpack(">B", params)
        parsed = {"arm": bool(arm), "force": False}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_ARMING | ARM: {bool(arm)}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 2:
        arm, force = struct.unpack(">BB", params)
        parsed = {"arm": bool(arm), "force": bool(force)}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_ARMING | ARM: {bool(arm)}, FORCE: {bool(force)}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_ARMING | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_takeoff(cmd_id, params, src_id, interface):
    if len(params) == 4:
        altitude_m, = struct.unpack(">f", params)
        parsed = {"altitude_m": altitude_m, "min_pitch_deg": 0.0}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_TAKEOFF | ALT: {altitude_m:.2f} m")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 8:
        altitude_m, min_pitch_deg = struct.unpack(">ff", params)
        parsed = {"altitude_m": altitude_m, "min_pitch_deg": min_pitch_deg}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_TAKEOFF | ALT: {altitude_m:.2f} m, PITCH: {min_pitch_deg:.2f} deg")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_TAKEOFF | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_land(cmd_id, params, src_id, interface):
    if len(params) == 0:
        parsed = {"mode": 0, "lat": None, "lon": None, "yaw": None}
        logger.info("[COMMAND] RECV | CMD: FLIGHT_LAND | MODE: NORMAL")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 21: # mode(B) + lat(d) + lon(d) + yaw(f)
        mode, lat, lon, yaw = struct.unpack(">Bddf", params)
        parsed = {"mode": mode, "lat": lat, "lon": lon, "yaw": yaw}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_LAND | TARGET: LAT={lat:.6f}, LON={lon:.6f}, YAW={yaw:.2f}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_LAND | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_goto(cmd_id, params, src_id, interface):
    if len(params) == 20: # lat(d) + lon(d) + alt(f) = 8 + 8 + 4 = 20
        lat, lon, alt = struct.unpack(">ddf", params)
        parsed = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": 0} # Default alt_ref
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_GOTO | TARGET: LAT={lat:.6f}, LON={lon:.6f}, ALT={alt:.2f}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 21: # lat(d) + lon(d) + alt(f) + alt_ref(B) = 8 + 8 + 4 + 1 = 21
        lat, lon, alt, alt_ref = struct.unpack(">ddfB", params)
        parsed = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": alt_ref}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_GOTO | TARGET: LAT={lat:.6f}, LON={lon:.6f}, ALT={alt:.2f}, REF={alt_ref}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_GOTO | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_speed(cmd_id, params, src_id, interface):
    if len(params) == 4:
        speed_mps, = struct.unpack(">f", params)
        parsed = {"speed_mps": speed_mps, "scope": 0} # Default scope
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_SPEED | SPEED: {speed_mps}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 5:
        speed_mps, scope = struct.unpack(">fB", params)
        parsed = {"speed_mps": speed_mps, "scope": scope}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_SPEED | SPEED: {speed_mps}, SCOPE: {scope}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_SPEED | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_roi(cmd_id, params, src_id, interface):
    if not params:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | Parameters are empty")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
        return

    roi_mode = params[0]
    parsed = {"roi_mode": roi_mode}

    if roi_mode == 0: # CLEAR
        if len(params) == 1:
            logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_ROI | MODE: CLEAR")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        else:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | CLEAR mode expects 1 byte, got {len(params)}")
            # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

    elif roi_mode == 1: # LOCATION
        if len(params) == 17: # mode + lat + lon
            lat, lon = struct.unpack(">dd", params[1:])
            parsed.update({"lat": lat, "lon": lon, "alt_m": 0.0}) # Default alt
            logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_ROI | MODE: LOCATION, LAT: {lat:.6f}, LON: {lon:.6f}")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        elif len(params) == 21: # mode + lat + lon + alt
            lat, lon, alt_m = struct.unpack(">ddf", params[1:])
            parsed.update({"lat": lat, "lon": lon, "alt_m": alt_m})
            logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_ROI | MODE: LOCATION, LAT: {lat:.6f}, LON: {lon:.6f}, ALT: {alt_m:.2f}")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        else:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | LOCATION mode expects 17 or 21 bytes, got {len(params)}")
            # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | Unknown roi_mode: {roi_mode}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_home(cmd_id, params, src_id, interface):
    if len(params) == 0:
        parsed = {"lat": None, "lon": None} # Use current location
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_HOME | MODE: CURRENT")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 16: # lat(d) + lon(d) = 8 + 8 = 16
        lat, lon = struct.unpack(">dd", params)
        parsed = {"lat": lat, "lon": lon}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_HOME | LAT: {lat:.6f}, LON: {lon:.6f}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_HOME | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_altitude(cmd_id, params, src_id, interface):
    if len(params) == 4:
        alt_m, = struct.unpack(">f", params)
        parsed = {"alt_m": alt_m, "alt_ref": 0} # Default alt_ref
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_ALTITUDE | ALT: {alt_m:.2f}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 5:
        alt_m, alt_ref = struct.unpack(">fB", params)
        parsed = {"alt_m": alt_m, "alt_ref": alt_ref}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_ALTITUDE | ALT: {alt_m:.2f}, REF: {alt_ref}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ALTITUDE | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def flight_set_heading(cmd_id, params, src_id, interface):
    if len(params) == 5:
        mode, yaw_deg = struct.unpack(">Bf", params)
        parsed = {"mode": mode, "yaw_deg": yaw_deg, "turn": 0} # Default turn
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_HEADING | MODE: {mode}, YAW: {yaw_deg:.2f}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    elif len(params) == 6:
        mode, yaw_deg, turn = struct.unpack(">Bfb", params)
        parsed = {"mode": mode, "yaw_deg": yaw_deg, "turn": turn}
        logger.info(f"[COMMAND] RECV | CMD: FLIGHT_SET_HEADING | MODE: {mode}, YAW: {yaw_deg:.2f}, TURN: {turn}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_HEADING | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def mission_upload(cmd_id, params, src_id, interface):
    """Gelen MISSION_UPLOAD komutunu işler."""
    try:
        if not params:
            raise ValueError("Parameters are empty")

        data = json.loads(params.decode('utf-8'))
        mission_id = data.get("mission_id")
        waypoints = data.get("waypoints", [])
        
        if mission_id is None:
            raise ValueError("`mission_id` is missing")

        parsed = {"mission_id": mission_id, "waypoints": waypoints, "replace_existing": data.get("replace_existing", True)}
        
        logger.info(f"[COMMAND] RECV | CMD: MISSION_UPLOAD | ID: {mission_id}, WP_COUNT: {len(waypoints)}")
        set_last_command(cmd_id, params, parsed)
        
        # send_ack_ok(interface, cmd_id, dst=src_id)

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: MISSION_UPLOAD | ERROR: {e}")
        send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def mission_control(cmd_id, params, src_id, interface):
    """Gelen MISSION_CONTROL komutunu işler."""
    try:
        if not params:
            raise ValueError("Parameters are empty")

        data = json.loads(params.decode('utf-8'))
        action = data.get("action")

        if not action:
            raise ValueError("`action` is missing")

        parsed = {"action": action, "start_index": data.get("start_index"), "abort_mode": data.get("abort_mode")}
        
        logger.info(f"[COMMAND] RECV | CMD: MISSION_CONTROL | ACTION: {action}")
        set_last_command(cmd_id, params, parsed)
        
        # send_ack_ok(interface, cmd_id, dst=src_id)

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: MISSION_CONTROL | ERROR: {e}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)

def swarm_formation_execute(cmd_id, params, src_id, interface):
    try:
        if not params:
            raise ValueError("Parameters are empty")

        data = json.loads(params.decode('utf-8'))
        leader_id = data.get("leader_id")
        formation_type = data.get("formation_type")

        if leader_id is None or formation_type is None:
            raise ValueError("`leader_id` or `formation_type` is missing")

        logger.info(f"[COMMAND] RECV | CMD: SWARM_FORMATION_EXECUTE | LEADER: {leader_id}, FORMATION: {formation_type}")
        set_last_command(cmd_id, params, data)
        # send_ack_ok(interface, cmd_id, dst=src_id)

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_FORMATION_EXECUTE | ERROR: {e}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)


def swarm_set_leader(cmd_id, params, src_id, interface):
    if len(params) == 4:
        leader_id, = struct.unpack(">I", params)
        parsed = {"leader_id": leader_id}
        logger.info(f"[COMMAND] RECV | CMD: SWARM_SET_LEADER | ID: {leader_id}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_LEADER | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)


def swarm_set_formation_type(cmd_id, params, src_id, interface):
    if params:
        try:
            formation_type = params.decode('utf-8')
            parsed = {"formation_type": formation_type}
            logger.info(f"[COMMAND] RECV | CMD: SWARM_SET_FORMATION_TYPE | TYPE: {formation_type}")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_FORMATION_TYPE | Could not decode formation type string")
            # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_FORMATION_TYPE")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)


def swarm_set_spacing(cmd_id, params, src_id, interface):
    if len(params) == 8:
        spacing_offset, = struct.unpack(">d", params)
        parsed = {"spacing_offset": spacing_offset}
        logger.info(f"[COMMAND] RECV | CMD: SWARM_SET_SPACING | OFFSET: {spacing_offset}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_SPACING | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)


def swarm_set_altitude_offset(cmd_id, params, src_id, interface):
    if len(params) == 8:
        altitude_offset, = struct.unpack(">d", params)
        parsed = {"altitude_offset": altitude_offset}
        logger.info(f"[COMMAND] RECV | CMD: SWARM_SET_ALTITUDE_OFFSET | OFFSET: {altitude_offset}")
        set_last_command(cmd_id, params, parsed)
        # send_ack_ok(interface, cmd_id, dst=src_id)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_ALTITUDE_OFFSET | PRM LEN: {len(params)}")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)


def swarm_set_status(cmd_id, params, src_id, interface):
    if params:
        try:
            status = params.decode('utf-8')
            parsed = {"status": status}
            logger.info(f"[COMMAND] RECV | CMD: SWARM_SET_STATUS | STATUS: {status}")
            set_last_command(cmd_id, params, parsed)
            # send_ack_ok(interface, cmd_id, dst=src_id)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_STATUS | Could not decode status string")
            # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_STATUS")
        # send_ack_invalid_cmd(interface, cmd_id, dst=src_id)
