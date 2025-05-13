# src/serializers/ack_serializer.py

import struct
from src.tools.log.logger import logger

# Status code to name mapping
STATUS_NAMES = {
    0: "SUCCESS",
    1: "INVALID_PARAMS",
    2: "UNSUPPORTED"
}

def serialize_ack(command_id: int, status_code: int, is_ack: bool = True, ftp: bool = False) -> bytes:
    """
    Builds an ACK or NACK message.
    If ftp=True, status_code is packed as 4 bytes; otherwise as 1 byte.
    """
    # Komut adını almak için import işlemini fonksiyon içinde yap (circular import önlemi)
    from src.handlers.command.command_handler import command_definitions, CommandDefinition

    ack_code = 0xAA if is_ack else 0xFF

    if ftp:
        # payload: ack_code(1B), cmd_id(1B), status_code(4B)
        payload = struct.pack(">BBI", ack_code, command_id, status_code)
    else:
        # payload: ack_code(1B), cmd_id(1B), status_code(1B)
        payload = struct.pack(">BBB", ack_code, command_id, status_code)

    ack_type = "ACK" if is_ack else "NACK"
    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")

    # Komut adını bul
    cmd_def = command_definitions.get(command_id, CommandDefinition(f"CMD_{command_id}", None))
    cmd_name = cmd_def.name

    logger.debug(
        f"[ACK] SERIALIZED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_name}"
        f"{' (FTP)' if ftp else ''}"
    )

    return payload

def deserialize_ack(payload: bytes, ftp: bool = False) -> dict:
    """
    Parses an ACK or NACK message.
    If ftp=True, expects a 6-byte payload; otherwise 3-byte.
    Returns dict with keys: ack_code, command_id, status_code.
    """
    expected_len = 6 if ftp else 3
    if len(payload) != expected_len:
        logger.warning(f"[ACK] Invalid payload length: {len(payload)} (expected {expected_len})")
        raise ValueError("Invalid ACK payload length")

    if ftp:
        # payload: [0]=ack_code, [1]=cmd_id, [2:6]=status_code (4B)
        ack_code    = payload[0]
        command_id  = payload[1]
        status_code = struct.unpack(">I", payload[2:6])[0]
    else:
        ack_code, command_id, status_code = struct.unpack(">BBB", payload)

    # Komut adını almak için import burada yapılır (circular import önlemi)
    try:
        from src.handlers.command.command_handler import command_definitions, CommandDefinition
        cmd_def = command_definitions.get(command_id, CommandDefinition(f"CMD_{command_id}", None))
        cmd_name = cmd_def.name
    except ImportError:
        cmd_name = f"CMD_{command_id}"

    ack_type = "ACK" if ack_code == 0xAA else "NACK"
    status_name = STATUS_NAMES.get(status_code, f"UNKNOWN({status_code})")

    logger.debug(
        f"[ACK] DESERIALIZED | TYPE: {ack_type} | CMD: {cmd_name} | STATUS: {status_name}"
        f"{' (FTP)' if ftp else ''}"
    )

    return {
        "ack_code": ack_code,
        "command_id": command_id,
        "status_code": status_code
    }
