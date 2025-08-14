from __future__ import annotations
from src.application.command.serializer.dispatcher import deserialize_command
from src.application.command.definitions import command_definitions
from src.shared.log.logger import logger

def unknown(cmd_id: int, params: bytes, src_id: int, interface=None):
    logger.warning(f"[COMMAND] Unknown command ID {cmd_id} from SRC: {src_id} | PARAMS: {params.hex()}")

def handle_command(payload: bytes, frame_meta: dict, interface=None):
    """
    Parse and handle an incoming 'C' (Command) frame.

    Args:
        payload (bytes): Raw command payload.
        frame_meta (dict): Frame metadata including src_id, dst_id, etc.
        interface: Optional interface object to allow response sending.
    """
    try:
        src_id = frame_meta.get("src_id")
        data = deserialize_command(payload)

        cmd_id = data.get("command_id")
        params = data.get("params")

        if not isinstance(cmd_id, int):
            raise ValueError(f"Invalid command ID type: {type(cmd_id)}")

        if not isinstance(params, bytes):
            raise ValueError(f"Invalid parameters format: expected bytes, got {type(params)}")

        cmd_def = command_definitions.get(cmd_id)
        if cmd_def:
            logger.info(f"[COMMAND] RECEIVED | CMD: {cmd_id} ({cmd_def.name}) FROM SRC: {src_id} | PRM: {params.hex()}")
            cmd_def.handler(cmd_id, params, src_id, interface)
        else:
            unknown(cmd_id, params, src_id, interface)

    except Exception as e:
        logger.error(f"[COMMAND] ERROR | Failed to handle command: {e}")
        logger.debug(f"[COMMAND] Exception detail:", exc_info=True)
