from __future__ import annotations
from typing import Any, Dict, Optional
from lynk.shared.log.logger import logger

_PB = None

def _get_pb():
    global _PB
    if _PB is not None:
        return _PB
        
    import sys
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    proto_dir = os.path.join(root_dir, "lynk/shared/proto")
    if proto_dir not in sys.path:
        sys.path.append(proto_dir)

    try:
        from lynk.shared.proto.msg.event import event_envelope_pb2 as event_pb
        _PB = event_pb
        return _PB
    except Exception as exc:
        raise RuntimeError(
            "Event protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc

_EVENT_MAP = None

def _get_event_map():
    global _EVENT_MAP
    if _EVENT_MAP is not None:
        return _EVENT_MAP
    
    event_pb = _get_pb()
    _EVENT_MAP = {}
    
    envelope_desc = event_pb.EventEnvelope.DESCRIPTOR
    payload_oneof = envelope_desc.oneofs_by_name.get("payload")
    
    if not payload_oneof:
        logger.error("[EVENT] EventEnvelope 'payload' oneof not found!")
        return _EVENT_MAP

    for field in payload_oneof.fields:
        event_id = field.number
        field_name = field.name
        
        param_list = []
        if field.message_type:
            param_list = [f.name for f in field.message_type.fields]
             
        _EVENT_MAP[event_id] = (field_name, param_list)
        
    logger.debug(f"[EVENT] Loaded {len(_EVENT_MAP)} events from Protobuf introspection")
    return _EVENT_MAP


def get_event_payload_schema():
    """
    Public, stable accessor for event payload schema.

    Returns:
        dict[int, tuple[str, list[str]]]: event_type -> (oneof field name, payload field names)
    """
    event_map = _get_event_map()
    # Return a detached copy so callers cannot mutate shared internal cache.
    return {
        int(event_id): (str(field_name), list(fields))
        for event_id, (field_name, fields) in event_map.items()
    }

def serialize_event(
    event_type: int,
    priority: Optional[int] = None,
    transaction_id: Optional[str] = None,
    payload_params: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Serializes an event into a protobuf payload.
    
    Parameters:
        event_type (int): Event type ID (20-100)
        priority (int): Optional event priority (0-3), defaults to 0
        transaction_id (str): Optional transaction correlation id
        payload_params (dict): Event-specific parameters
        
    Returns:
        bytes: Serialized event
    """
    if payload_params is None:
        payload_params = {}

    event_map = _get_event_map()
    if event_type not in event_map:
        raise ValueError(f"Unsupported event type for protobuf: {event_type}")

    field_name, field_list = event_map[event_type]
    event_pb = _get_pb()
    envelope = event_pb.EventEnvelope()
    
    envelope.event_type = event_type
    envelope.priority = int(priority or 0)
    envelope.transaction_id = str(transaction_id or "")
    
    payload_msg = getattr(envelope, field_name)
    payload_msg.SetInParent()
    for key in field_list:
        if key in payload_params and payload_params[key] is not None:
            val = payload_params[key]
            # Check if this is a map field (like metadata)
            field_attr = getattr(payload_msg, key)
            if hasattr(field_attr, "update") and isinstance(val, dict):
                field_attr.update(val)
            else:
                setattr(payload_msg, key, val)

    data = envelope.SerializeToString()
    logger.debug(f"[EVENT] SERIALIZED | TYPE: {event_type} | TX_ID: {transaction_id} | SIZE={len(data)}B")
    return data

def deserialize_event(payload: bytes) -> dict:
    """
    Deserializes a protobuf payload into event structure.
    
    Parameters:
        payload (bytes): Received binary event payload
        
    Returns:
        dict: {
            "event_type": int,
            "priority": int,
            "transaction_id": str,
            "payload": dict
        }
    """
    if len(payload) == 0:
        logger.warning("[EVENT] Deserialization failed: Empty payload")
        raise ValueError("Payload must be at least 1 byte")

    event_map = _get_event_map()
    event_pb = _get_pb()
    envelope = event_pb.EventEnvelope()
    envelope.ParseFromString(payload)

    event_type = envelope.event_type
    which = envelope.WhichOneof("payload")

    result = {
        "event_type": event_type,
        "priority": int(getattr(envelope, "priority", 0) or 0),
        "transaction_id": str(getattr(envelope, "transaction_id", "") or ""),
    }

    if event_type not in event_map or not which:
        logger.warning(f"[EVENT] Unknown or unmapped event type: {event_type}")
        result["payload"] = {}
        return result

    field_list = event_map[event_type][1]
    msg = getattr(envelope, which)
    params = {key: getattr(msg, key) for key in field_list}

    logger.debug(f"[EVENT] DESERIALIZED | TYPE: {event_type} | TX_ID: {result.get('transaction_id', '')}")
    result["payload"] = params
    return result
