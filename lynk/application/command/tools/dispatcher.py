from __future__ import annotations
import uuid
import threading
# lynk/application/command/tools/dispatcher.py

"""
Command Dispatcher Module

Defines high‐level command functions that build and send specific command frames
over a communication interface, while logging each action.
"""

import struct
from typing import Any, Dict, List, Optional, Protocol

from lynk.application.command.tools.builder import (
    build_cmd_system_reboot,
    build_cmd_flight_set_mode,
    build_cmd_flight_takeoff,
    build_cmd_flight_goto,
    build_cmd_flight_set_speed,
    build_cmd_flight_set_altitude,
    build_cmd_flight_set_heading,
    build_cmd_flight_set_home,
    build_cmd_flight_set_roi,
    build_cmd_flight_land,
    build_cmd_flight_arming,
    build_cmd_system_set_vehicle_id,
    build_cmd_system_set_team_id,
    build_cmd_mission_upload, 
    build_cmd_mission_control,
    build_cmd_swarm_formation_execute,
    build_cmd_swarm_set_leader,
    build_cmd_swarm_set_formation_type,
    build_cmd_swarm_set_spacing,
    build_cmd_swarm_set_altitude_offset,
    build_cmd_swarm_set_status
)
from lynk.shared.comm.transmitter import send_frame
from lynk.shared.log.logger import logger
from lynk.application.ack.tools.dispatcher import send_ack_ok, send_ack_invalid_cmd
from lynk.application.command.tools.cache import set_last_command

_TX_CMD_MAP: Dict[str, str] = {}
_TX_CMD_ID_MAP: Dict[str, int] = {}
_TX_LOCK = threading.Lock()

def _register_tx_cmd(tx_id: str, cmd_name: str, cmd_id: int) -> None:
    if not tx_id:
        return
    with _TX_LOCK:
        _TX_CMD_MAP[tx_id] = cmd_name
        _TX_CMD_ID_MAP[tx_id] = cmd_id

def get_tx_cmd_name(tx_id: str) -> Optional[str]:
    if not tx_id:
        return None
    with _TX_LOCK:
        return _TX_CMD_MAP.get(tx_id)

def get_tx_cmd_id(tx_id: str) -> Optional[int]:
    if not tx_id:
        return None
    with _TX_LOCK:
        return _TX_CMD_ID_MAP.get(tx_id)


def get_command_schema() -> Dict[int, Dict[str, Any]]:
    """
    Public command schema view for integrations.

    Returns:
        {
          <cmd_id>: {
            "name": "<COMMAND_NAME>",
            "field_name": "<protobuf_field_name>",
            "param_names": [ ... ]
          },
          ...
        }
    """
    from lynk.application.command.serializer.dispatcher import _get_cmd_map

    cmd_map = _get_cmd_map() or {}
    schema: Dict[int, Dict[str, Any]] = {}
    for cmd_id, value in cmd_map.items():
        field_name, param_names = value
        command_name = str(field_name or "").upper()
        schema[int(cmd_id)] = {
            "name": command_name,
            "field_name": str(field_name or ""),
            "param_names": [str(p) for p in (param_names or [])],
        }
    return schema

def send_command(
    interface,
    command: str | int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    wait_for_ack: bool = False,
    ack_timeout: float = 2.0,
    callback: Optional[Any] = None,
    max_retries: int = 0,
    retry_interval: float = 2.0,
    transaction_id: Optional[str] = None,
    _retry_count: int = 0,
    _accumulated_results: Optional[Dict[int, str]] = None,
    **params
) -> Optional[Any]:
    """
    Generic command sender with Swarm ACK support and async callbacks.
    """
    from lynk.application.command.serializer.dispatcher import _get_cmd_map
    from lynk.application.command.tools.builder import build_cmd_frame
    from lynk.application.ack.tools.tracker import get_ack_tracker
    from lynk.application.telemetry.tools.cache import get_active_device_ids, get_device_hop_count
    
    cmd_map = _get_cmd_map()
    command_id = None
    
    if isinstance(command, int):
        command_id = command
    else:
        cmd_name_upper = command.upper()
        for cid, (field_name, _) in cmd_map.items():
            if field_name.upper() == cmd_name_upper:
                command_id = cid
                break
    
    if command_id is None or command_id not in cmd_map:
        raise ValueError(f"Unknown command: {command}")
    
    field_name, _ = cmd_map[command_id]
    
    # Use provided UUID or generate one (empty string should generate)
    final_tx_id = transaction_id if transaction_id else str(uuid.uuid4())
    
    _register_tx_cmd(final_tx_id, field_name.upper(), command_id)

    # Identify target nodes for ACK tracking
    expected_ids = []
    if dst != 0xFF:
        # Unicast
        expected_ids = [dst]
    else:
        # Broadcast
        # If dst_team_id is 0 or None, it's a global broadcast (all active devices)
        # If dst_team_id is X, it's a team broadcast
        expected_ids = get_active_device_ids(team_id=dst_team_id)

    # Adaptive Timeout Calculation
    # We find the furthest node (max hops) and increase timeout accordingly.
    # Base penalty: 0.5s per hop (round-trip factor)
    max_hops = 0
    if expected_ids:
        max_hops = max([get_device_hop_count(sid) for sid in expected_ids] or [0])
    
    hop_penalty = max_hops * 0.5
    adjusted_timeout = ack_timeout + hop_penalty
    
    if max_hops > 0:
        logger.info(f"[COMMAND] Adaptive Timeout: {ack_timeout}s + {hop_penalty}s (hops={max_hops}) = {adjusted_timeout:.1f}s")
    # Results container that persists across retries
    if _accumulated_results is None:
        _accumulated_results = {}
    
    # Event to signal complete finish (all nodes responded OR max retries reached)
    completion_event = threading.Event()

    def handle_session_result(current_results):
        nonlocal _retry_count
        _accumulated_results.update(current_results)
        missing = [sid for sid in expected_ids if sid not in _accumulated_results]
        
        if missing and _retry_count < max_retries:
            color = "\033[94m\033[1m"
            reset = "\033[0m"
            retry_for = field_name.upper() if field_name else f"CMD_ID:{command_id}"
            logger.info(f"{color}[COMMAND] SMART RETRY {_retry_count + 1}/{max_retries} FOR: {retry_for} | TARGETS: {missing}{reset}")
            
            # Targeted Unicast Re-send
            for node_id in missing:
                retry_frame = build_cmd_frame(command_id, params, node_id, src, team_id=dst_team_id, transaction_id=final_tx_id)
                send_frame(interface, retry_frame)
            
            _retry_count += 1
            
            tracker.register_session(
                final_tx_id, 
                missing, 
                callback=handle_session_result, 
                timeout=retry_interval
            )
        else:
            # Done with everything
            if callback:
                try:
                    callback(_accumulated_results)
                except Exception as e:
                    logger.error(f"[COMMAND] User callback error: {e}")
            completion_event.set()

    # Register with tracker if callback provided or waiting for ACK
    tracker = get_ack_tracker()
    tracker_registered = False
    if callback or wait_for_ack:
        if expected_ids:
            tracker.register_session(final_tx_id, expected_ids, callback=handle_session_result, timeout=adjusted_timeout)
            tracker_registered = True
        else:
            logger.warning(f"[COMMAND] No active devices found for tracking ACK of {command}")
            completion_event.set() # Nothing to track

    # Build and send initial frame
    frame = build_cmd_frame(command_id, params, dst, src, team_id=dst_team_id, transaction_id=final_tx_id)
    send_frame(interface, frame)
    
    from lynk.core.frame_codec import load_device_id
    src_id = src if src is not None else load_device_id()
    target = f"DST: {dst}" if dst_team_id is None else f"DST: {dst} @ TEAM: {dst_team_id}"
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.info(
        f"{color}[COMMAND] SENT | TYPE: {field_name.upper()} | SRC: {src_id} -> {target} | TX_ID: {final_tx_id}{reset}"
    )
    logger.debug(f"[COMMAND] Dispatching {field_name.upper()} | TX_ID: {final_tx_id} | WAIT={wait_for_ack}")

    if wait_for_ack and tracker_registered:
        # Block until the completion event is set by the (potentially recursive) callback
        total_max_wait = adjusted_timeout + (max_retries * retry_interval) + 1.0
        finished = completion_event.wait(timeout=total_max_wait)
        if not finished:
            logger.warning(f"[COMMAND] wait_for_ack timed out after {total_max_wait}s")
        return _accumulated_results

    return None



class SendableInterface(Protocol):
    """
    Protocol for a communication interface that supports send().
    """
    def send(self, frame: bytes) -> None: ...


def cmd_system_reboot(
    interface: SendableInterface,
    dst: int,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a SYSTEM_REBOOT command to reset the target device.
    """
    send_command(
        interface, "SYSTEM_REBOOT",
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_flight_set_mode(
    interface: SendableInterface,
    mode: str,
    dst: int,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a FLIGHT_SET_MODE command.
    """
    send_command(
        interface, "FLIGHT_SET_MODE",
        mode=mode,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_flight_arming(
    interface: SendableInterface,
    arm: bool,
    force: bool = False,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a FLIGHT_ARMING command.
    """
    send_command(
        interface, "FLIGHT_ARMING",
        arm=arm,
        force=force,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_flight_takeoff(
    interface: SendableInterface,
    altitude_m: float,
    min_pitch_deg: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a FLIGHT_TAKEOFF command.
    """
    send_command(
        interface, "FLIGHT_TAKEOFF",
        altitude_m=altitude_m,
        min_pitch_deg=min_pitch_deg,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_flight_land(
    interface: SendableInterface,
    mode: int = 0,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None,
    yaw: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a FLIGHT_LAND command.
    """
    has_target = target_lat is not None and target_lon is not None
    send_command(
        interface, "FLIGHT_LAND",
        mode=mode,
        has_target=has_target,
        lat=target_lat if has_target else 0.0,
        lon=target_lon if has_target else 0.0,
        yaw=yaw if yaw is not None else 0.0,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_flight_goto(
    interface: SendableInterface,
    lat: float,
    lon: float,
    alt: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a FLIGHT_GOTO command to navigate to a waypoint.
    """
    send_command(
        interface, "FLIGHT_GOTO",
        lat=lat,
        lon=lon,
        alt=alt,
        alt_ref=alt_ref,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_flight_set_speed(
    interface: SendableInterface,
    speed_mps: float,
    scope: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "FLIGHT_SET_SPEED",
        speed_mps=speed_mps,
        scope=scope,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_flight_set_altitude(
    interface: SendableInterface,
    alt_m: float,
    alt_ref: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "FLIGHT_SET_ALTITUDE",
        alt_m=alt_m,
        alt_ref=alt_ref,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_flight_set_heading(
    interface: SendableInterface,
    mode: int,
    yaw_deg: float,
    turn: Optional[int] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "FLIGHT_SET_HEADING",
        mode=mode,
        yaw_deg=yaw_deg,
        turn=turn,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_flight_set_roi(
    interface: SendableInterface,
    roi_mode: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    alt_m: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "FLIGHT_SET_ROI",
        roi_mode=roi_mode,
        lat=lat,
        lon=lon,
        alt_m=alt_m,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_flight_set_home(
    interface: SendableInterface,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    use_current = lat is None or lon is None
    send_command(
        interface, "FLIGHT_SET_HOME",
        use_current=use_current,
        lat=lat if lat is not None else 0.0,
        lon=lon if lon is not None else 0.0,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_mission_upload(
    interface: SendableInterface,
    mission_id: int,
    waypoints: list,
    replace_existing: bool = True,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a MISSION_UPLOAD command.
    """
    import json
    payload = {
        "mission_id": mission_id,
        "waypoints": waypoints,
        "replace_existing": replace_existing
    }
    json_str = json.dumps(payload, separators=(',', ':'))
    
    send_command(
        interface, "MISSION_UPLOAD",
        json=json_str,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )


def cmd_mission_control(
    interface: SendableInterface,
    action: str,
    start_index: Optional[int] = None,
    abort_mode: Optional[str] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    """
    Send a MISSION_CONTROL command.
    """
    send_command(
        interface, "MISSION_CONTROL",
        action=action,
        start_index=start_index,
        abort_mode=abort_mode,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_system_set_vehicle_id(
    interface: SendableInterface,
    id: int,
    persist: bool = False,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SYSTEM_SET_VEHICLE_ID",
        vehicle_id=id,
        persist=bool(persist),
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_system_set_team_id(
    interface: SendableInterface,
    team_id: int,
    persist: bool = False,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SYSTEM_SET_TEAM_ID",
        team_id=team_id,
        persist=bool(persist),
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_formation_execute(
    interface: SendableInterface,
    leader_id: int,
    formation_type: str,
    spacing_offset: Optional[float] = None,
    altitude_offset: Optional[float] = None,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_FORMATION_EXECUTE",
        leader_id=leader_id,
        formation_type=formation_type,
        spacing_offset=spacing_offset if spacing_offset is not None else 0.0,
        altitude_offset=altitude_offset if altitude_offset is not None else 0.0,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_set_leader(
    interface: SendableInterface,
    leader_id: int,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_SET_LEADER",
        leader_id=leader_id,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_set_formation_type(
    interface: SendableInterface,
    formation_type: str,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_SET_FORMATION_TYPE",
        formation_type=formation_type,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_set_spacing(
    interface: SendableInterface,
    spacing_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_SET_SPACING",
        spacing_offset=spacing_offset,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_set_altitude_offset(
    interface: SendableInterface,
    altitude_offset: float,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_SET_ALTITUDE_OFFSET",
        altitude_offset=altitude_offset,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )

def cmd_swarm_set_status(
    interface: SendableInterface,
    status: str,
    dst: int = 0xFF,
    src: Optional[int] = None,
    dst_team_id: Optional[int] = None,
    transaction_id: str = "",
    wait_for_ack: bool = False,
    max_retries: int = 0,
    **kwargs
) -> None:
    send_command(
        interface, "SWARM_SET_STATUS",
        status=status,
        dst=dst,
        src=src,
        dst_team_id=dst_team_id,
        transaction_id=transaction_id,
        wait_for_ack=wait_for_ack,
        max_retries=max_retries,
        **kwargs
    )
