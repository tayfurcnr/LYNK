from __future__ import annotations
from lynk.application.ack.serializer.dispatcher import deserialize_ack
from lynk.application.ack.definitions import ack_definitions
from lynk.shared.log.logger import logger
import lynk.application.ack.handler.impl as handler
from lynk.shared.utils.dedupe import DedupeCache

_ACK_DEDUPE = DedupeCache(ttl_sec=2.0)

def handle_ack(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'A' (ACK) type frame.
    """
    try:
        src_id = frame_meta.get("src_id")
        dst_id = frame_meta.get("dst_id")
        data = deserialize_ack(payload)
        ack_id = data.get("ack_id")
        tx_id = data.get("transaction_id", "")

        if not isinstance(ack_id, int):
            raise ValueError(f"Invalid ACK ID: {ack_id}")

        ack_def = ack_definitions.get(ack_id, None)
        if ack_def:
            try:
                from lynk.application.ack.tools.dispatcher import _format_for
                cmd_id = data.get("cmd_id")
                for_part = f"  FOR: {_format_for(cmd_id)}" if cmd_id is not None else ""
            except Exception:
                for_part = ""
            color = "\033[93m\033[1m"
            reset = "\033[0m"
            key = (tx_id, src_id, ack_id)
            if _ACK_DEDUPE.allow(key):
                logger.info(f"{color}[ACK] RECV | TYPE: {ack_def.name}{for_part} | SRC: {src_id} -> DST: {dst_id} | TX_ID: {tx_id}{reset}")
            ack_def.handler(data, src_id)
        else:
            handler.unknown(data, src_id, ack_id)

    except ValueError as ve:
        logger.error(f"[ACK] Invalid ACK format: {ve}")
        logger.debug(f"[ACK] Error details: {ve}", exc_info=True)

    except Exception as e:
        logger.error(f"[ACK] Exception during ACK parsing: {e}")
        logger.debug(f"[ACK] Full exception: {e}", exc_info=True)
