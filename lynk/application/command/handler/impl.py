from __future__ import annotations
# lynk/handlers/command_handler.py

from lynk.shared.log.logger import logger

def _log_recv(msg: str) -> None:
    logger.debug(msg)
from lynk.application.command.tools.cache import set_last_command
import struct
import json

# === INDIVIDUAL COMMAND HANDLERS ===
def _is_dict_params(params) -> bool:
    return isinstance(params, dict)

def default_handler(cmd_id: int, params: dict | bytes, src_id: int, interface, cmd_name: str = ""):
    """
    Default command handler for commands without a specific implementation.
    Acknowledge the command and log for bridge forwarding.
    """
    label = (cmd_name or f"CMD_ID:{cmd_id}").upper()
    if isinstance(params, dict):
        parsed = dict(params)
        _log_recv(f"[COMMAND] RECV | TYPE: {label} | PARAMS: {parsed}")
    elif isinstance(params, (bytes, bytearray)):
        parsed = {"raw_params_hex": bytes(params).hex()}
        _log_recv(f"[COMMAND] RECV | TYPE: {label} | RAW_HEX: {parsed['raw_params_hex']}")
    else:
        parsed = {}
        _log_recv(f"[COMMAND] RECV | TYPE: {label}")
    set_last_command(cmd_id, params, parsed)

def system_reboot(cmd_id, params, src_id, interface):
    _log_recv("[COMMAND] RECV | TYPE: SYSTEM_REBOOT")
    set_last_command(cmd_id, params, {})

def _handle_vehicle_id_update(vehicle_id: int, cmd_id, params, persist: bool):
    """Helper to update vehicle ID in runtime config and optionally persist."""
    from lynk.shared.config.manager import get_config, save_config
    get_config()["vehicle"]["id"] = vehicle_id
    parsed = {"id": vehicle_id, "persist": bool(persist)}
    _log_recv(
        f"[COMMAND] RECV | TYPE: SYSTEM_SET_VEHICLE_ID | ID updated to: {vehicle_id} | PERSIST: {bool(persist)}"
    )
    if persist:
        save_config()
    set_last_command(cmd_id, params, parsed)

def system_set_vehicle_id(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        vehicle_id = params.get("vehicle_id")
        if vehicle_id is None:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_VEHICLE_ID | vehicle_id missing")
            return
        persist = bool(params.get("persist", False))
        _handle_vehicle_id_update(vehicle_id, cmd_id, params, persist)
    elif len(params) == 4:
        vehicle_id, = struct.unpack(">I", params)
        _handle_vehicle_id_update(vehicle_id, cmd_id, params, False)
    elif len(params) == 5:
        vehicle_id, persist = struct.unpack(">IB", params)
        _handle_vehicle_id_update(vehicle_id, cmd_id, params, bool(persist))
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_VEHICLE_ID | PRM LEN: {len(params)}")

def _handle_team_id_update(team_id: int, cmd_id, params, persist: bool):
    """Helper to update team ID in runtime config and optionally persist."""
    from lynk.shared.config.manager import get_config, save_config
    get_config()["vehicle"]["team_id"] = team_id
    parsed = {"team_id": team_id, "persist": bool(persist)}
    _log_recv(f"[COMMAND] RECV | TYPE: SYSTEM_SET_TEAM_ID | Team ID updated to: {team_id} | PERSIST: {bool(persist)}")
    if persist:
        save_config()
    set_last_command(cmd_id, params, parsed)

def system_set_team_id(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        team_id = params.get("team_id")
        if team_id is None:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_TEAM_ID | team_id missing")
            return
        persist = bool(params.get("persist", False))
        _handle_team_id_update(team_id, cmd_id, params, persist)
    elif len(params) == 1:
        team_id, = struct.unpack(">B", params)
        _handle_team_id_update(team_id, cmd_id, params, False)
    elif len(params) == 2:
        team_id, persist = struct.unpack(">BB", params)
        _handle_team_id_update(team_id, cmd_id, params, bool(persist))
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SYSTEM_SET_TEAM_ID | PRM LEN: {len(params)}")

def flight_set_mode(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        mode = params.get("mode")
        if not mode:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_MODE | mode missing")
            return
        parsed = {"mode": mode}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_MODE | MODE: {mode}")
        set_last_command(cmd_id, params, parsed)
    elif params:
        try:
            mode = params.decode('utf-8')
            parsed = {"mode": mode}
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_MODE | MODE: {mode}")
            set_last_command(cmd_id, params, parsed)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_MODE | Could not decode mode string")
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_MODE")

def flight_arming(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        arm = bool(params.get("arm", False))
        force = bool(params.get("force", False))
        parsed = {"arm": arm, "force": force}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_ARMING | ARM: {arm}, FORCE: {force}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 1:
        arm, = struct.unpack(">B", params)
        parsed = {"arm": bool(arm), "force": False}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_ARMING | ARM: {bool(arm)}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 2:
        arm, force = struct.unpack(">BB", params)
        parsed = {"arm": bool(arm), "force": bool(force)}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_ARMING | ARM: {bool(arm)}, FORCE: {bool(force)}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_ARMING | PRM LEN: {len(params)}")

def flight_takeoff(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        altitude_m = float(params.get("altitude_m", 0.0))
        min_pitch_deg = float(params.get("min_pitch_deg", 0.0))
        parsed = {"altitude_m": altitude_m, "min_pitch_deg": min_pitch_deg}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_TAKEOFF | ALT: {altitude_m:.2f} m, PITCH: {min_pitch_deg:.2f} deg")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 4:
        altitude_m, = struct.unpack(">f", params)
        parsed = {"altitude_m": altitude_m, "min_pitch_deg": 0.0}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_TAKEOFF | ALT: {altitude_m:.2f} m")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 8:
        altitude_m, min_pitch_deg = struct.unpack(">ff", params)
        parsed = {"altitude_m": altitude_m, "min_pitch_deg": min_pitch_deg}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_TAKEOFF | ALT: {altitude_m:.2f} m, PITCH: {min_pitch_deg:.2f} deg")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_TAKEOFF | PRM LEN: {len(params)}")

def flight_land(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        has_target = bool(params.get("has_target", False))
        mode = int(params.get("mode", 0))
        lat = float(params.get("lat", 0.0))
        lon = float(params.get("lon", 0.0))
        yaw = float(params.get("yaw", 0.0))
        parsed = {"mode": mode, "lat": lat if has_target else None, "lon": lon if has_target else None, "yaw": yaw if has_target else None}
        if has_target:
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_LAND | TARGET: LAT={lat:.6f}, LON={lon:.6f}, YAW={yaw:.2f}")
        else:
            _log_recv("[COMMAND] RECV | TYPE: FLIGHT_LAND | MODE: NORMAL")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 0:
        parsed = {"mode": 0, "lat": None, "lon": None, "yaw": None}
        _log_recv("[COMMAND] RECV | TYPE: FLIGHT_LAND | MODE: NORMAL")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 21: # mode(B) + lat(d) + lon(d) + yaw(f)
        mode, lat, lon, yaw = struct.unpack(">Bddf", params)
        parsed = {"mode": mode, "lat": lat, "lon": lon, "yaw": yaw}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_LAND | TARGET: LAT={lat:.6f}, LON={lon:.6f}, YAW={yaw:.2f}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_LAND | PRM LEN: {len(params)}")

def flight_goto(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        lat = float(params.get("lat", 0.0))
        lon = float(params.get("lon", 0.0))
        alt = float(params.get("alt", 0.0))
        alt_ref = int(params.get("alt_ref", 0))
        parsed = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": alt_ref}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_GOTO | TARGET: LAT={lat:.6f}, LON={lon:.6f}, ALT={alt:.2f}, REF={alt_ref}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 20: # lat(d) + lon(d) + alt(f) = 8 + 8 + 4 = 20
        lat, lon, alt = struct.unpack(">ddf", params)
        parsed = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": 0} # Default alt_ref
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_GOTO | TARGET: LAT={lat:.6f}, LON={lon:.6f}, ALT={alt:.2f}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 21: # lat(d) + lon(d) + alt(f) + alt_ref(B) = 8 + 8 + 4 + 1 = 21
        lat, lon, alt, alt_ref = struct.unpack(">ddfB", params)
        parsed = {"lat": lat, "lon": lon, "alt": alt, "alt_ref": alt_ref}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_GOTO | TARGET: LAT={lat:.6f}, LON={lon:.6f}, ALT={alt:.2f}, REF={alt_ref}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_GOTO | PRM LEN: {len(params)}")

def flight_set_speed(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        speed_mps = float(params.get("speed_mps", 0.0))
        scope = int(params.get("scope", 0))
        parsed = {"speed_mps": speed_mps, "scope": scope}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_SPEED | SPEED: {speed_mps}, SCOPE: {scope}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 4:
        speed_mps, = struct.unpack(">f", params)
        parsed = {"speed_mps": speed_mps, "scope": 0} # Default scope
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_SPEED | SPEED: {speed_mps}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 5:
        speed_mps, scope = struct.unpack(">fB", params)
        parsed = {"speed_mps": speed_mps, "scope": scope}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_SPEED | SPEED: {speed_mps}, SCOPE: {scope}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_SPEED | PRM LEN: {len(params)}")

def flight_set_roi(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        roi_mode = int(params.get("roi_mode", 0))
        parsed = {"roi_mode": roi_mode}
        if roi_mode == 0:
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ROI | MODE: CLEAR")
            set_last_command(cmd_id, params, parsed)
            return
        if roi_mode == 1:
            lat = float(params.get("lat", 0.0))
            lon = float(params.get("lon", 0.0))
            alt_m = float(params.get("alt_m", 0.0))
            parsed.update({"lat": lat, "lon": lon, "alt_m": alt_m})
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ROI | MODE: LOCATION, LAT: {lat:.6f}, LON: {lon:.6f}, ALT: {alt_m:.2f}")
            set_last_command(cmd_id, params, parsed)
            return
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | Unknown roi_mode: {roi_mode}")
        return
    if not params:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | Parameters are empty")
        return

    roi_mode = params[0]
    parsed = {"roi_mode": roi_mode}

    if roi_mode == 0: # CLEAR
        if len(params) == 1:
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ROI | MODE: CLEAR")
            set_last_command(cmd_id, params, parsed)
        else:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | CLEAR mode expects 1 byte, got {len(params)}")

    elif roi_mode == 1: # LOCATION
        if len(params) == 17: # mode + lat + lon
            lat, lon = struct.unpack(">dd", params[1:])
            parsed.update({"lat": lat, "lon": lon, "alt_m": 0.0}) # Default alt
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ROI | MODE: LOCATION, LAT: {lat:.6f}, LON: {lon:.6f}")
            set_last_command(cmd_id, params, parsed)
        elif len(params) == 21: # mode + lat + lon + alt
            lat, lon, alt_m = struct.unpack(">ddf", params[1:])
            parsed.update({"lat": lat, "lon": lon, "alt_m": alt_m})
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ROI | MODE: LOCATION, LAT: {lat:.6f}, LON: {lon:.6f}, ALT: {alt_m:.2f}")
            set_last_command(cmd_id, params, parsed)
        else:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | LOCATION mode expects 17 or 21 bytes, got {len(params)}")
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ROI | Unknown roi_mode: {roi_mode}")

def flight_set_home(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        use_current = bool(params.get("use_current", False))
        lat = float(params.get("lat", 0.0))
        lon = float(params.get("lon", 0.0))
        if use_current:
            parsed = {"lat": None, "lon": None}
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HOME | MODE: CURRENT")
        else:
            parsed = {"lat": lat, "lon": lon}
            _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HOME | LAT: {lat:.6f}, LON: {lon:.6f}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 0:
        parsed = {"lat": None, "lon": None} # Use current location
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HOME | MODE: CURRENT")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 16: # lat(d) + lon(d) = 8 + 8 = 16
        lat, lon = struct.unpack(">dd", params)
        parsed = {"lat": lat, "lon": lon}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HOME | LAT: {lat:.6f}, LON: {lon:.6f}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_HOME | PRM LEN: {len(params)}")

def flight_set_altitude(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        alt_m = float(params.get("alt_m", 0.0))
        alt_ref = int(params.get("alt_ref", 0))
        parsed = {"alt_m": alt_m, "alt_ref": alt_ref}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ALTITUDE | ALT: {alt_m:.2f}, REF: {alt_ref}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 4:
        alt_m, = struct.unpack(">f", params)
        parsed = {"alt_m": alt_m, "alt_ref": 0} # Default alt_ref
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ALTITUDE | ALT: {alt_m:.2f}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 5:
        alt_m, alt_ref = struct.unpack(">fB", params)
        parsed = {"alt_m": alt_m, "alt_ref": alt_ref}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_ALTITUDE | ALT: {alt_m:.2f}, REF: {alt_ref}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_ALTITUDE | PRM LEN: {len(params)}")

def flight_set_heading(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        mode = int(params.get("mode", 0))
        yaw_deg = float(params.get("yaw_deg", 0.0))
        turn = int(params.get("turn", 0))
        parsed = {"mode": mode, "yaw_deg": yaw_deg, "turn": turn}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HEADING | MODE: {mode}, YAW: {yaw_deg:.2f}, TURN: {turn}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 5:
        mode, yaw_deg = struct.unpack(">Bf", params)
        parsed = {"mode": mode, "yaw_deg": yaw_deg, "turn": 0} # Default turn
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HEADING | MODE: {mode}, YAW: {yaw_deg:.2f}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 6:
        mode, yaw_deg, turn = struct.unpack(">Bfb", params)
        parsed = {"mode": mode, "yaw_deg": yaw_deg, "turn": turn}
        _log_recv(f"[COMMAND] RECV | TYPE: FLIGHT_SET_HEADING | MODE: {mode}, YAW: {yaw_deg:.2f}, TURN: {turn}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: FLIGHT_SET_HEADING | PRM LEN: {len(params)}")

def mission_upload(cmd_id, params, src_id, interface):
    """Gelen MISSION_UPLOAD komutunu işler."""
    try:
        if _is_dict_params(params):
            raw_json = params.get("json")
            if not raw_json:
                raise ValueError("json is missing")
            data = json.loads(raw_json)
        else:
            if not params:
                raise ValueError("Parameters are empty")
            data = json.loads(params.decode('utf-8'))
        mission_id = data.get("mission_id")
        waypoints = data.get("waypoints", [])
        
        if mission_id is None:
            raise ValueError("`mission_id` is missing")

        parsed = {
            "mission_id": mission_id,
            "waypoints": waypoints,
            "replace_existing": data.get("replace_existing", True),
            "camera_type": data.get("camera_type"),
            "palette": data.get("palette"),
            "start_index": data.get("start_index"),
        }
        
        _log_recv(f"[COMMAND] RECV | TYPE: MISSION_UPLOAD | ID: {mission_id}, WP_COUNT: {len(waypoints)}")
        set_last_command(cmd_id, params, parsed)
        

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: MISSION_UPLOAD | ERROR: {e}")

def mission_control(cmd_id, params, src_id, interface):
    """Gelen MISSION_CONTROL komutunu işler."""
    try:
        if _is_dict_params(params):
            raw_json = params.get("json")
            if not raw_json:
                raise ValueError("json is missing")
            data = json.loads(raw_json)
        else:
            if not params:
                raise ValueError("Parameters are empty")
            data = json.loads(params.decode('utf-8'))
        action = data.get("action")

        if not action:
            raise ValueError("`action` is missing")

        parsed = {"action": action, "start_index": data.get("start_index"), "abort_mode": data.get("abort_mode")}
        
        _log_recv(f"[COMMAND] RECV | TYPE: MISSION_CONTROL | ACTION: {action}")
        set_last_command(cmd_id, params, parsed)
        

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: MISSION_CONTROL | ERROR: {e}")

def swarm_formation_execute(cmd_id, params, src_id, interface):
    try:
        if _is_dict_params(params):
            leader_id = params.get("leader_id")
            formation_type = params.get("formation_type")
            data = {
                "leader_id": leader_id,
                "formation_type": formation_type,
                "spacing_offset": params.get("spacing_offset"),
                "altitude_offset": params.get("altitude_offset"),
            }
        else:
            if not params:
                raise ValueError("Parameters are empty")
            data = json.loads(params.decode('utf-8'))
            leader_id = data.get("leader_id")
            formation_type = data.get("formation_type")

        if leader_id is None or formation_type is None:
            raise ValueError("`leader_id` or `formation_type` is missing")

        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_FORMATION_EXECUTE | LEADER: {leader_id}, FORMATION: {formation_type}")
        set_last_command(cmd_id, params, data)

    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_FORMATION_EXECUTE | ERROR: {e}")


def swarm_set_leader(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        leader_id = params.get("leader_id")
        if leader_id is None:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_LEADER | leader_id missing")
            return
        parsed = {"leader_id": leader_id}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_LEADER | ID: {leader_id}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 4:
        leader_id, = struct.unpack(">I", params)
        parsed = {"leader_id": leader_id}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_LEADER | ID: {leader_id}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_LEADER | PRM LEN: {len(params)}")


def swarm_set_formation_type(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        formation_type = params.get("formation_type")
        if not formation_type:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_FORMATION_TYPE | formation_type missing")
            return
        parsed = {"formation_type": formation_type}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_FORMATION_TYPE | TYPE: {formation_type}")
        set_last_command(cmd_id, params, parsed)
    elif params:
        try:
            formation_type = params.decode('utf-8')
            parsed = {"formation_type": formation_type}
            _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_FORMATION_TYPE | TYPE: {formation_type}")
            set_last_command(cmd_id, params, parsed)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_FORMATION_TYPE | Could not decode formation type string")
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_FORMATION_TYPE")


def swarm_set_spacing(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        spacing_offset = params.get("spacing_offset")
        if spacing_offset is None:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_SPACING | spacing_offset missing")
            return
        parsed = {"spacing_offset": spacing_offset}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_SPACING | OFFSET: {spacing_offset}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 8:
        spacing_offset, = struct.unpack(">d", params)
        parsed = {"spacing_offset": spacing_offset}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_SPACING | OFFSET: {spacing_offset}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_SPACING | PRM LEN: {len(params)}")


def swarm_set_altitude_offset(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        altitude_offset = params.get("altitude_offset")
        if altitude_offset is None:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_ALTITUDE_OFFSET | altitude_offset missing")
            return
        parsed = {"altitude_offset": altitude_offset}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_ALTITUDE_OFFSET | OFFSET: {altitude_offset}")
        set_last_command(cmd_id, params, parsed)
    elif len(params) == 8:
        altitude_offset, = struct.unpack(">d", params)
        parsed = {"altitude_offset": altitude_offset}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_ALTITUDE_OFFSET | OFFSET: {altitude_offset}")
        set_last_command(cmd_id, params, parsed)
    else:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_ALTITUDE_OFFSET | PRM LEN: {len(params)}")


def swarm_set_status(cmd_id, params, src_id, interface):
    if _is_dict_params(params):
        status = params.get("status")
        if not status:
            logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_STATUS | status missing")
            return
        parsed = {"status": status}
        _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_STATUS | STATUS: {status}")
        set_last_command(cmd_id, params, parsed)
    elif params:
        try:
            status = params.decode('utf-8')
            parsed = {"status": status}
            _log_recv(f"[COMMAND] RECV | TYPE: SWARM_SET_STATUS | STATUS: {status}")
            set_last_command(cmd_id, params, parsed)
        except UnicodeDecodeError:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: SWARM_SET_STATUS | Could not decode status string")
    else:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: SWARM_SET_STATUS")


def _handle_dict_command(cmd_id, params, cmd_name: str, required_keys=None):
    if not _is_dict_params(params):
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: {cmd_name} | expected dict, got {type(params).__name__}")
        return
    required_keys = required_keys or []
    missing = [k for k in required_keys if params.get(k) is None]
    if missing:
        logger.warning(f"[COMMAND] INVALID PARAMS | CMD: {cmd_name} | missing: {missing}")
        return
    parsed = dict(params)
    _log_recv(f"[COMMAND] RECV | TYPE: {cmd_name} | PARAMS: {parsed}")
    set_last_command(cmd_id, params, parsed)


def gimbal_set_mode(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "GIMBAL_SET_MODE", required_keys=["mode"])


def gimbal_set_attitude(cmd_id, params, src_id, interface):
    _handle_dict_command(
        cmd_id, params, "GIMBAL_SET_ATTITUDE", required_keys=["yaw_deg", "pitch_deg", "roll_deg", "speed"]
    )


def gimbal_set_velocity(cmd_id, params, src_id, interface):
    _handle_dict_command(
        cmd_id, params, "GIMBAL_SET_VELOCITY", required_keys=["yaw_rate_dps", "pitch_rate_dps", "roll_rate_dps"]
    )


def gimbal_stop(cmd_id, params, src_id, interface):
    _log_recv("[COMMAND] RECV | TYPE: GIMBAL_STOP")
    set_last_command(cmd_id, params, {})


def gimbal_home(cmd_id, params, src_id, interface):
    _log_recv("[COMMAND] RECV | TYPE: GIMBAL_HOME")
    set_last_command(cmd_id, params, {})


def gimbal_track_target_control(cmd_id, params, src_id, interface):
    if not _is_dict_params(params):
        logger.warning("[COMMAND] INVALID PARAMS | CMD: GIMBAL_TRACK_TARGET_CONTROL | expected dict")
        return
    if params.get("enable") is None:
        logger.warning("[COMMAND] INVALID PARAMS | CMD: GIMBAL_TRACK_TARGET_CONTROL | missing: ['enable']")
        return
    if bool(params.get("enable")):
        required_when_enabled = ["video_type", "x0", "y0", "x1", "y1"]
        missing = [k for k in required_when_enabled if params.get(k) is None]
        if missing:
            logger.warning(f"[COMMAND] INVALID PARAMS | CMD: GIMBAL_TRACK_TARGET_CONTROL | missing: {missing}")
            return
    parsed = dict(params)
    _log_recv(f"[COMMAND] RECV | TYPE: GIMBAL_TRACK_TARGET_CONTROL | PARAMS: {parsed}")
    set_last_command(cmd_id, params, parsed)


def gimbal_seek_position(cmd_id, params, src_id, interface):
    _handle_dict_command(
        cmd_id, params, "GIMBAL_SEEK_POSITION", required_keys=["target_yaw", "target_pitch", "target_roll", "speed", "tolerance"]
    )


def gimbal_calibrate(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "GIMBAL_CALIBRATE", required_keys=["calibration_type"])


def camera_take_photo(cmd_id, params, src_id, interface):
    _log_recv("[COMMAND] RECV | TYPE: CAMERA_TAKE_PHOTO")
    set_last_command(cmd_id, params, {})


def camera_record_control(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "CAMERA_RECORD_CONTROL", required_keys=["enable"])


def camera_set_digital_zoom(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "CAMERA_SET_DIGITAL_ZOOM", required_keys=["level"])


def camera_set_white_balance(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "CAMERA_SET_WHITE_BALANCE", required_keys=["mode"])


def thermal_set_false_color(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "THERMAL_SET_FALSE_COLOR", required_keys=["palette"])


def camera_stream_control(cmd_id, params, src_id, interface):
    _handle_dict_command(cmd_id, params, "CAMERA_STREAM_CONTROL", required_keys=["stream_type", "enable"])


def gimbal_get_sd_capacity(cmd_id, params, src_id, interface):
    _log_recv("[COMMAND] RECV | TYPE: GIMBAL_GET_SD_CAPACITY")
    set_last_command(cmd_id, params, {})
