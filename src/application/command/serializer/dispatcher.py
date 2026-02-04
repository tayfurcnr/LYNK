from __future__ import annotations
# src/command/serializer/dispatcher.py

from typing import Any, Dict, Optional

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
        from src.shared.proto.msg.command import command_envelope_pb2 as cmd_pb
        _PB = cmd_pb
        return _PB
    except Exception as exc:
        raise RuntimeError(
            "Command protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc

_CMD_MAP = None

def _get_cmd_map():
    global _CMD_MAP
    if _CMD_MAP is not None:
        return _CMD_MAP
    
    cmd_pb = _get_pb()
    _CMD_MAP = {}
    
    # Introspect CommandEnvelope to find payload fields
    envelope_desc = cmd_pb.CommandEnvelope.DESCRIPTOR
    payload_oneof = envelope_desc.oneofs_by_name.get("payload")
    
    if not payload_oneof:
        logger.error("[DISPATCHER] CommandEnvelope 'payload' oneof not found!")
        return _CMD_MAP

    for field in payload_oneof.fields:
        cmd_id = field.number
        field_name = field.name
        
        # Get parameter names from the inner message definition
        param_list = []
        if field.message_type:
             param_list = [f.name for f in field.message_type.fields]
             
        _CMD_MAP[cmd_id] = (field_name, param_list)
        
    logger.debug(f"[DISPATCHER] Loaded {_CMD_MAP} commands from Protobuf introspection")
    return _CMD_MAP

def serialize_command(command_id: int, params: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Serializes a command into a protobuf payload.

    Parameters:
        command_id (int): The command identifier (0–255)
        params (dict): Command parameters mapped to protobuf fields.

    Returns:
        bytes: Serialized command [command_id] + [params]
    """
    if params is None:
        params = {}

    cmd_map = _get_cmd_map()
    if command_id not in cmd_map:
        raise ValueError(f"Unsupported command ID for protobuf: {command_id}")

    field_name, field_list = cmd_map[command_id]
    cmd_pb = _get_pb()
    envelope = cmd_pb.CommandEnvelope()
    envelope.cmd_id = command_id # Should now map to field 255 in protobuf definition
    payload_msg = getattr(envelope, field_name)
    payload_msg.SetInParent()
    for key in field_list:
        if key in params:
            setattr(payload_msg, key, params[key])

    data = envelope.SerializeToString()
    logger.debug(f"[COMMAND] SERIALIZED | CMD_ID: {command_id} | SIZE={len(data)}B")
    return data

def deserialize_command(payload: bytes) -> dict:
    """
    Deserializes a protobuf payload into command structure.

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

    cmd_map = _get_cmd_map()
    cmd_pb = _get_pb()
    envelope = cmd_pb.CommandEnvelope()
    envelope.ParseFromString(payload)

    command_id = envelope.cmd_id
    which = envelope.WhichOneof("payload")

    # If the ID is unknown or the payload part is missing/unmapped
    if command_id not in cmd_map or not which:
        logger.warning(f"[COMMAND] Unknown or unmapped command ID: {command_id}")
        return {"command_id": command_id, "params": payload} # Return raw payload as params

    field_list = cmd_map[command_id][1]
    msg = getattr(envelope, which)
    params = {key: getattr(msg, key) for key in field_list}

    logger.debug(f"[COMMAND] DESERIALIZED | CMD_ID: {command_id} | PARAMS: {list(params.keys())}")

    return {"command_id": command_id, "params": params}
