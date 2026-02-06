from __future__ import annotations
# /src/ack/tools/dispatcher.py

"""
ACK Dispatcher Module

Constructs and sends various ACK frames over a communication interface.
Each function serializes a specific ACK payload, builds a full LYNK frame,
and transmits it, while logging the action for traceability.
"""

from src.application.ack.serializer.dispatcher import serialize_ack
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger
from src.core.frame_codec import build_mesh_frame, load_device_id

def _cmd_name(cmd_id: int) -> str | None:
    try:
        from src.application.command.definitions import command_definitions
        defn = command_definitions.get(cmd_id)
        return defn.name if defn else None
    except Exception:
        return None

def _format_for(cmd_id: int) -> str:
    name = _cmd_name(cmd_id)
    return name if name else f"CMD_ID:{cmd_id}"

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
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.info(
        f"{color}[ACK] SENT | TYPE: ACK_OK  FOR: {_format_for(cmd_id)} | SRC: {src} -> DST: {dst} | TX_ID: {transaction_id}{reset}"
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
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_ERROR  FOR: {_format_for(cmd_id)} | SRC: {src} -> DST: {dst} | TX_ID: {transaction_id}{reset}"
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
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.warning(
        f"{color}[ACK] SENT | TYPE: ACK_BUSY  FOR: {_format_for(cmd_id)} | SRC: {src} -> DST: {dst} | TX_ID: {transaction_id}{reset}"
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
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_EXECUTION_ERROR  FOR: {_format_for(cmd_id)} | SRC: {src} -> DST: {dst} | TX_ID: {transaction_id}{reset}"
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
    frame = build_mesh_frame('A', src, dst, payload)
    send_frame(interface, frame)
    color = "\033[96m\033[1m"
    reset = "\033[0m"
    logger.error(
        f"{color}[ACK] SENT | TYPE: ACK_INVALID_CMD  FOR: {_format_for(cmd_id)} | SRC: {src} -> DST: {dst} | TX_ID: {transaction_id}{reset}"
    )
