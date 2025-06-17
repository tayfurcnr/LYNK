# src/ack/handler/impl.py

from src.tools.log.logger import logger

def ack_ok(data: dict, src_id: int):
    logger.info(f"[ACK] ACK_OK received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_error(data: dict, src_id: int):
    logger.error(f"[ACK] ACK_ERROR received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_busy(data: dict, src_id: int):
    logger.warning(f"[ACK] ACK_BUSY received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def ack_invalid_cmd(data: dict, src_id: int):
    logger.error(f"[ACK] ACK_INVALID_CMD received from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")

def unknown(data: dict, src_id: int, ack_id: int):
    logger.warning(f"[ACK] Unknown ACK ID {ack_id} from SRC: {src_id}")
    logger.debug(f"[ACK] → Data: {data}")