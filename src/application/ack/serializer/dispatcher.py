from __future__ import annotations
# src/ack/serializer/dispatcher.py

from src.shared.log.logger import logger

_PB = None

def _get_pb():
    global _PB
    if _PB is not None:
        return _PB
            
    import sys
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    proto_dir = os.path.join(root_dir, "src/shared/proto")
    if proto_dir not in sys.path:
        sys.path.append(proto_dir)

    try:
        from src.shared.proto.msg.ack import ack_envelope_pb2 as ack_pb
    except Exception as exc:
        raise RuntimeError(
            "ACK protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc
    _PB = ack_pb
    return _PB

_ACK_MAP = None

def _get_ack_map():
    global _ACK_MAP
    if _ACK_MAP is not None:
        return _ACK_MAP
    _ACK_MAP = {
        "ACK_OK": ("ok", ["cmd_id"]),
        "ACK_ERROR": ("error", ["cmd_id"]),
        "ACK_BUSY": ("busy", ["cmd_id"]),
        "ACK_INVALID_CMD": ("invalid_cmd", ["cmd_id"]),
        "ACK_EXECUTION_ERROR": ("execution_error", ["cmd_id"]),
    }
    return _ACK_MAP

def serialize_ack(name: str, transaction_id: str, *params) -> bytes:
    """
    Serialize ACK data by ACK name using protobuf payloads.
    """
    from src.application.ack.definitions import ack_definitions
    for defn in ack_definitions.values():
        if defn.name == name:
            ack_id = defn.id
            break
    else:
        raise ValueError(f"ACK name not found: {name}")

    ack_map = _get_ack_map()
    if name not in ack_map:
        raise ValueError(f"ACK schema not mapped: {name}")

    ack_pb = _get_pb()
    field_name, field_list = ack_map[name]
    if len(params) != len(field_list):
        raise ValueError(f"{name} expects {len(field_list)} params, got {len(params)}")

    envelope = ack_pb.AckEnvelope()
    envelope.ack_id = ack_id
    envelope.transaction_id = transaction_id
    payload_msg = getattr(envelope, field_name)
    for key, value in zip(field_list, params):
        setattr(payload_msg, key, value)

    data = envelope.SerializeToString()
    logger.debug(f"[ACK] SERIALIZED | NAME: {name} | ID={ack_id} | TX_ID={transaction_id} | SIZE={len(data)}B")
    return data

def deserialize_ack(payload: bytes) -> dict:
    """
    Deserialize an ACK payload using protobuf.

    Returns:
        dict: {"ack_id": int, "transaction_id": str, "name": str, ...fields }
    """
    if not payload:
        raise ValueError("Payload too short")

    from src.application.ack.definitions import ack_definitions
    ack_pb = _get_pb()
    envelope = ack_pb.AckEnvelope()
    envelope.ParseFromString(payload)

    aid = envelope.ack_id
    tid = envelope.transaction_id
    defn = ack_definitions.get(aid)
    if not defn:
        raise ValueError(f"Unknown ACK ID: {aid}")

    which = envelope.WhichOneof("payload")
    if not which:
        raise ValueError("ACK payload missing")

    ack_map = _get_ack_map()
    field_list = ack_map[defn.name][1]
    msg = getattr(envelope, which)
    fields = {key: getattr(msg, key) for key in field_list}
    logger.debug(
        f"[ACK] DESERIALIZED | NAME: {defn.name} | ID=0x{aid:02X} | TX_ID={tid} | FIELDS={list(fields.keys())}"
    )

    return {"ack_id": aid, "transaction_id": tid, **fields}
