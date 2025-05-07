# src/serializers/ack_serializer.py

from src.tools.log.logger import logger

# Status code to name mapping
STATUS_NAMES = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}

def serialize_ack(command_id: int, status_code: int, is_ack: bool = True) -> bytes:
    """
    Builds an ACK or NACK message.
    """
    # ✅ Komut adını almak için import işlemini fonksiyon içinde yap
    from src.handlers.command.command_handler import command_definitions, CommandDefinition

    ack_code = 0xAA if is_ack else 0xFF
    payload = bytes([ack_code, command_id, status_code])

    ack_type = "ACK" if is_ack else "NACK"
    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")

    # ✅ Komut adını bul
    cmd_def = command_definitions.get(command_id, CommandDefinition(f"CMD_{command_id}", None))
    cmd_name = cmd_def.name

    logger.debug(
        f"[ACK] SERIALIZED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_name}"
    )

    return payload


def deserialize_ack(payload: bytes) -> dict:
    """
    Parses an ACK or NACK message.
    """
    if len(payload) != 3:
        logger.warning(f"[ACK] Invalid payload length: {len(payload)}")
        raise ValueError("Invalid ACK payload length (expected 3 bytes)")

    data = {
        "ack_code": payload[0],
        "command_id": payload[1],
        "status_code": payload[2]
    }

    # Komut adını almak için import burada yapılır (circular import önlemi)
    try:
        from src.handlers.command.command_handler import command_definitions, CommandDefinition
        cmd_def = command_definitions.get(data["command_id"], CommandDefinition(f"CMD_{data['command_id']}", None))
        cmd_name = cmd_def.name
    except ImportError:
        cmd_name = f"CMD_{data['command_id']}"  # Yine de loglar bozulmasın diye yedek isim

    ack_type = "ACK" if data["ack_code"] == 0xAA else "NACK"
    status_name = STATUS_NAMES.get(data["status_code"], f"UNKNOWN({data['status_code']})")

    logger.debug(
        f"[ACK] DESERIALIZED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_name}"
    )

    return data
