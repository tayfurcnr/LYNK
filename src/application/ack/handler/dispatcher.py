from __future__ import annotations
from src.application.ack.serializer.dispatcher import deserialize_ack
from src.application.ack.definitions import ack_definitions
from src.shared.log.logger import logger
import src.application.ack.handler.impl as handler

def handle_ack(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'A' (ACK) type frame.
    """
    try:
        src_id = frame_meta.get("src_id")
        data = deserialize_ack(payload)
        ack_id = data.get("ack_id")

        if not isinstance(ack_id, int):
            raise ValueError(f"Invalid ACK ID: {ack_id}")

        ack_def = ack_definitions.get(ack_id, None)
        if ack_def:
            logger.debug(f"[ACK] RECEIVED | ACK_ID: {ack_id} ({ack_def.name}) FROM SRC: {src_id}")
            ack_def.handler(data, src_id)
        else:
            handler.unknown(data, src_id, ack_id)

    except ValueError as ve:
        logger.error(f"[ACK] Invalid ACK format: {ve}")
        logger.debug(f"[ACK] Error details: {ve}", exc_info=True)

    except Exception as e:
        logger.error(f"[ACK] Exception during ACK parsing: {e}")
        logger.debug(f"[ACK] Full exception: {e}", exc_info=True)