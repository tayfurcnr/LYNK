# src/serializers/command_serializer.py

from src.tools.log.logger import logger  # Optional: Remove if logging not needed

def serialize_command(command_id: int, params: bytes = b'') -> bytes:
    """
    Serializes a command into a binary payload.

    Parameters:
        command_id (int): The command identifier (0–255)
        params (bytes): Optional parameters to include in the payload

    Returns:
        bytes: Serialized command [command_id] + [params]
    """
    payload = bytes([command_id]) + params
    logger.debug(f"[COMMAND] SERIALIZED | CMD_ID: {command_id} | PARAM_LEN: {len(params)}")
    return payload

def deserialize_command(payload: bytes) -> dict:
    """
    Deserializes a binary payload into command structure.

    Parameters:
        payload (bytes): Received binary command payload

    Returns:
        dict: {
            "command_id": int,
            "params": bytes
        }
    """
    if len(payload) == 0:
        logger.warning("[COMMAND] Deserialization failed: Empty payload")
        raise ValueError("Payload must be at least 1 byte")

    command_id = payload[0]
    params = payload[1:] if len(payload) > 1 else b''

    logger.debug(f"[COMMAND] DESERIALIZED | CMD_ID: {command_id} | PARAM_LEN: {len(params)}")

    return {
        "command_id": command_id,
        "params": params
    }
