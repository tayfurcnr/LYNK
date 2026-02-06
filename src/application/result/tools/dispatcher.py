from __future__ import annotations
# src/application/result/tools/dispatcher.py

from typing import Optional
from src.application.result.serializer.dispatcher import serialize_result
from src.shared.comm.transmitter import send_frame
from src.shared.log.logger import logger
from src.core.frame_codec import build_mesh_frame, load_device_id

def send_result(
    interface,
    tx_id: str,
    status: str,
    error_code: Optional[int] = None,
    message: Optional[str] = None,
    dst: int = 0xFF,
    src: int | None = None
) -> None:
    """
    Send a result frame ('R') for a previously received command.
    """
    if src is None:
        src = load_device_id()
    payload = serialize_result(tx_id, status, error_code=error_code, message=message)
    frame = build_mesh_frame('R', src, dst, payload)
    send_frame(interface, frame)

    color = "\033[96m\033[1m"
    reset = "\033[0m"
    cmd_part = ""
    try:
        from src.application.command.tools.dispatcher import get_tx_cmd_name, get_tx_cmd_id
        cmd_name = get_tx_cmd_name(tx_id)
        if cmd_name:
            cmd_part = f"  FOR: {cmd_name}"
        else:
            cmd_id = get_tx_cmd_id(tx_id)
            if cmd_id is not None:
                cmd_part = f"  FOR: CMD_ID:{cmd_id}"
    except Exception:
        cmd_part = ""
    logger.info(
        f"{color}[RESULT] SENT | TYPE: RESULT  STATUS: {status.upper()}{cmd_part} | SRC: {src} -> DST: {dst} | TX_ID: {tx_id}{reset}"
    )
