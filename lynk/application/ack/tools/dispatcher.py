from __future__ import annotations
# /lynk/ack/tools/dispatcher.py

"""
ACK Dispatcher Module

Constructs and sends various ACK frames over a communication interface.
Each function serializes a specific ACK payload, builds a full LYNK frame,
and transmits it, while logging the action for traceability.
"""

from lynk.application.ack.serializer.dispatcher import serialize_ack
from lynk.shared.comm.transmitter import send_frame
from lynk.shared.log.logger import logger
from lynk.core.frame_codec import build_mesh_frame, load_device_id, load_team_id
from lynk.shared.config.manager import get as get_cfg

def _cmd_name(cmd_id: int) -> str | None:
    try:
        from lynk.application.command.definitions import command_definitions
        defn = command_definitions.get(cmd_id)
        return defn.name if defn else None
    except Exception:
        return None

def _format_for(cmd_id: int) -> str:
    name = _cmd_name(cmd_id)
    return name if name else f"CMD_ID:{cmd_id}"

def _get_ack_mode() -> tuple[str, int]:
    mode = get_cfg("ack.mode", "unicast")
    if not isinstance(mode, str):
        mode = "unicast"
    mode = mode.lower().strip()
    if mode not in ("unicast", "broadcast", "both"):
        mode = "unicast"
    bcast_team_id = get_cfg("ack.broadcast_team_id", None)
    if bcast_team_id is None:
        bcast_team_id = load_team_id()
    return mode, int(bcast_team_id)

def _send_ack_frames(
    interface,
    payload: bytes,
    src: int,
    dst: int,
) -> tuple[str, str]:
    mode, bcast_team_id = _get_ack_mode()
    if mode in ("unicast", "both"):
        frame = build_mesh_frame('A', src, dst, payload)
        send_frame(interface, frame)
    if mode in ("broadcast", "both"):
        frame = build_mesh_frame('A', src, 0xFF, payload, team_id=bcast_team_id)
        send_frame(interface, frame)

    if mode == "unicast":
        return "MODE: UNICAST", f"DST: {dst}"
    if mode == "broadcast":
        return "MODE: BROADCAST", f"DST: 255"
    return "MODE: UNI+BCAST", f"DST: {dst} | BCAST: 255"

def send_ack_ok(
    interface,
    transaction_id: str,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_OK frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_OK", transaction_id, cmd_id)
    mode_note, dst_note = _send_ack_frames(interface, payload, src, dst)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.info(
        f"{color}[ACK] SENT | TYPE: ACK_OK  FOR: {_format_for(cmd_id)} | SRC: {src} -> {dst_note} | TX_ID: {transaction_id} | {mode_note}{reset}"
    )


def send_ack_error(
    interface,
    transaction_id: str,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_ERROR frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_ERROR", transaction_id, cmd_id)
    mode_note, dst_note = _send_ack_frames(interface, payload, src, dst)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_ERROR  FOR: {_format_for(cmd_id)} | SRC: {src} -> {dst_note} | TX_ID: {transaction_id} | {mode_note}{reset}"
    )


def send_ack_busy(
    interface,
    transaction_id: str,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_BUSY frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_BUSY", transaction_id, cmd_id)
    mode_note, dst_note = _send_ack_frames(interface, payload, src, dst)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.warning(
        f"{color}[ACK] SENT | TYPE: ACK_BUSY  FOR: {_format_for(cmd_id)} | SRC: {src} -> {dst_note} | TX_ID: {transaction_id} | {mode_note}{reset}"
    )

def send_ack_execution_error(
    interface,
    transaction_id: str,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_EXECUTION_ERROR frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_EXECUTION_ERROR", transaction_id, cmd_id)
    mode_note, dst_note = _send_ack_frames(interface, payload, src, dst)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_EXECUTION_ERROR  FOR: {_format_for(cmd_id)} | SRC: {src} -> {dst_note} | TX_ID: {transaction_id} | {mode_note}{reset}"
    )


def send_ack_invalid_cmd(
    interface,
    transaction_id: str,
    cmd_id: int,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send an ACK_INVALID_CMD frame with the corresponding command ID.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_ack("ACK_INVALID_CMD", transaction_id, cmd_id)
    mode_note, dst_note = _send_ack_frames(interface, payload, src, dst)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_INVALID_CMD  FOR: {_format_for(cmd_id)} | SRC: {src} -> {dst_note} | TX_ID: {transaction_id} | {mode_note}{reset}"
    )
