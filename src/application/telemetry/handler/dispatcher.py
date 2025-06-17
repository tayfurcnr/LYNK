from src.application.telemetry.serializer.dispatcher import deserialize_telemetry
from src.application.telemetry.definitions import telemetry_definitions
from src.shared.log.logger import logger

def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")

def handle_telemetry(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'T' (Telemetry) type frame and update telemetry cache.
    """
    try:
        src_id = frame_meta.get("src_id")
        data = deserialize_telemetry(payload)
        tlm_id = data.get("tlm_id")

        if not isinstance(tlm_id, int):
            raise ValueError(f"Invalid telemetry ID: {tlm_id}")

        tlm_def = telemetry_definitions.get(tlm_id, None)
        if tlm_def:
            logger.info(f"[TELEMETRY] RECEIVED | TLM_ID: {tlm_id} ({tlm_def.name}) FROM SRC: {src_id}")
            tlm_def.handler(data, src_id)
        else:
            unknown(data, src_id, tlm_id)

    except ValueError as ve:
        logger.error(f"[TELEMETRY] Invalid telemetry format: {ve}")
        logger.debug(f"[TELEMETRY] Error details: {ve}", exc_info=True)

    except Exception as e:
        logger.error(f"[TELEMETRY] Exception during telemetry parsing: {e}")
        logger.debug(f"[TELEMETRY] Full exception: {e}", exc_info=True)
