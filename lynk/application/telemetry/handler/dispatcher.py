from __future__ import annotations
from lynk.application.telemetry.serializer.dispatcher import deserialize_telemetry
from lynk.application.telemetry.definitions import telemetry_definitions
from lynk.shared.log.logger import logger

def unknown(data: dict, src_id: int, tlm_id: int):
    logger.warning(f"[TELEMETRY] Unknown telemetry ID {tlm_id} from SRC: {src_id}")

def handle_telemetry(payload: bytes, frame_meta: dict, interface=None):
    """
    Handle incoming 'T' (Telemetry) type frame and update telemetry cache.
    """
    try:
        src_id = frame_meta.get("src_id")
        team_id = frame_meta.get("team_id")
        hop_count = frame_meta.get("hop_count", 0)
        data = deserialize_telemetry(payload)
        tlm_id = data.get("tlm_id")

        if not isinstance(tlm_id, int):
            raise ValueError(f"Invalid telemetry ID: {tlm_id}")

        tlm_def = telemetry_definitions.get(tlm_id, None)
        if tlm_def:
            logger.debug(f"[TELEMETRY] RECEIVED | TLM_ID: {tlm_id} ({tlm_def.name}) FROM SRC: {src_id} | HOPS: {hop_count}")
            tlm_def.handler(data, src_id, team_id=team_id, hop_count=hop_count)
        else:
            # Check if we have a raw payload (meaning it's not even in Protobuf schema)
            if "raw_payload" in data:
                logger.warning(f"[TELEMETRY] Unknown Telemetry Format | ID: {tlm_id} from SRC: {src_id}")
                unknown(data, src_id, tlm_id)
                return

            # If it IS in schema but has no handler, use default_handler
            from lynk.application.telemetry.handler.impl import default_handler
            from lynk.application.telemetry.serializer.dispatcher import _get_tlm_fields
            
            tlm_fields = _get_tlm_fields()
            tlm_name = next((name for name, info in tlm_fields.items() if info[2] == tlm_id), None)
            
            if tlm_name:
                logger.debug(f"[TELEMETRY] RECEIVED | TLM_ID: {tlm_id} ({tlm_name}) FROM SRC: {src_id} | HOPS: {hop_count} (using default handler)")
                default_handler(data, src_id, tlm_name, team_id=team_id, hop_count=hop_count)
            else:
                unknown(data, src_id, tlm_id)

    except ValueError as ve:
        logger.error(f"[TELEMETRY] Invalid telemetry format: {ve}")
        logger.debug(f"[TELEMETRY] Error details: {ve}", exc_info=True)

    except Exception as e:
        logger.error(f"[TELEMETRY] Exception during telemetry parsing: {e}")
        logger.debug(f"[TELEMETRY] Full exception: {e}", exc_info=True)
