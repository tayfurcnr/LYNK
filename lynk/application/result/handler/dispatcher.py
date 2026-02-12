from __future__ import annotations
from lynk.application.result.serializer.dispatcher import deserialize_result
from lynk.shared.log.logger import logger

def handle_result(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'R' (Result) type frame.
    """
    try:
        src_id = frame_meta.get("src_id")
        dst_id = frame_meta.get("dst_id")
        data = deserialize_result(payload)
        status = data.get("status")
        tx_id = data.get("tx_id")
        message = data.get("message")
        error_code = data.get("error_code")

        if status == "FAILURE":
            color = "\033[95m\033[1m"
        elif status == "TIMEOUT":
            color = "\033[93m\033[1m"
        else:
            color = "\033[92m\033[1m"
        reset = "\033[0m"
        extra = ""
        if error_code is not None:
            extra += f" | ERR: {error_code}"
        if message:
            extra += f" | MSG: {message}"

        cmd_part = ""
        try:
            from lynk.application.command.tools.dispatcher import get_tx_cmd_name, get_tx_cmd_id
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
            f"{color}[RESULT] RECV | TYPE: RESULT  STATUS: {status}{cmd_part} | SRC: {src_id} -> DST: {dst_id} | TX_ID: {tx_id}{extra}{reset}"
        )
    except Exception as e:
        logger.error(f"[RESULT] ERROR | Failed to handle result: {e}")
        logger.debug("[RESULT] Exception detail:", exc_info=True)
