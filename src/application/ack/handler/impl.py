from __future__ import annotations
# src/ack/handler/impl.py

from src.shared.log.logger import logger

def ack_ok(data: dict, src_id: int):
    logger.debug(f"[ACK] → Data: {data}")
    from src.application.ack.tools.tracker import get_ack_tracker
    tid = data.get("transaction_id")
    if tid:
        get_ack_tracker().notify_ack(tid, src_id, "ACK_OK")

def ack_error(data: dict, src_id: int):
    logger.debug(f"[ACK] → Data: {data}")
    from src.application.ack.tools.tracker import get_ack_tracker
    tid = data.get("transaction_id")
    if tid:
        get_ack_tracker().notify_ack(tid, src_id, "ACK_ERROR")

def ack_busy(data: dict, src_id: int):
    logger.debug(f"[ACK] → Data: {data}")
    from src.application.ack.tools.tracker import get_ack_tracker
    tid = data.get("transaction_id")
    if tid:
        get_ack_tracker().notify_ack(tid, src_id, "ACK_BUSY")

def ack_invalid_cmd(data: dict, src_id: int):
    logger.debug(f"[ACK] → Data: {data}")
    from src.application.ack.tools.tracker import get_ack_tracker
    tid = data.get("transaction_id")
    if tid:
        get_ack_tracker().notify_ack(tid, src_id, "ACK_INVALID_CMD")

def ack_execution_error(data: dict, src_id: int):
    logger.debug(f"[ACK] → Data: {data}")
    from src.application.ack.tools.tracker import get_ack_tracker
    tid = data.get("transaction_id")
    if tid:
        get_ack_tracker().notify_ack(tid, src_id, "ACK_EXECUTION_ERROR")

def unknown(data: dict, src_id: int, ack_id: int):
    logger.warning(f"[ACK] Unknown ACK ID {ack_id} from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")
