from __future__ import annotations
# lynk/application/telemetry/serializer/dispatcher.py

from lynk.application.telemetry.definitions import telemetry_definitions
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
        from lynk.shared.proto.msg.telemetry import telemetry_envelope_pb2 as tlm_pb
        _PB = tlm_pb
        return _PB
    except Exception as exc:
        raise RuntimeError(
            "Telemetry protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc

_TLM_FIELDS = None

def _get_tlm_fields():
    global _TLM_FIELDS
    if _TLM_FIELDS is not None:
        return _TLM_FIELDS

    tlm_pb = _get_pb()
    _TLM_FIELDS = {}
    
    envelope_desc = tlm_pb.TelemetryEnvelope.DESCRIPTOR
    payload_oneof = envelope_desc.oneofs_by_name.get("payload")
    
    if not payload_oneof:
        logger.error("[DISPATCHER] TelemetryEnvelope 'payload' oneof not found!")
        return _TLM_FIELDS

    for field in payload_oneof.fields:
        # convention: field name 'gps' -> map key 'GPS'
        # we might need a better way if names don't match exactly inv-casing
        key_name = field.name.upper()
        
        param_list = []
        if field.message_type:
            param_list = [f.name for f in field.message_type.fields]
            
        # We store (field_name, param_list, id)
        _TLM_FIELDS[key_name] = (field.name, param_list, field.number)
        
    logger.debug(f"[DISPATCHER] Loaded {_TLM_FIELDS} telemetry schemas from Protobuf introspection")
    return _TLM_FIELDS

def serialize_telemetry(name: str, *params) -> bytes:
    """
    Serialize telemetry data by telemetry name using protobuf payloads.
    """
    tlm_fields = _get_tlm_fields()
    
    if name not in tlm_fields:
        # Fallback to definitions if not found (though definitions ideally match proto)
        # But we really need the field name and params from proto to serialize
        raise ValueError(f"Telemetry schema not mapped (proto missing?): {name}")

    field_name, field_list, tlm_id = tlm_fields[name]
    
    if len(params) != len(field_list):
        raise ValueError(f"{name} expects {len(field_list)} params, got {len(params)}")

    tlm_pb = _get_pb()
    envelope = tlm_pb.TelemetryEnvelope()
    envelope.tlm_id = tlm_id
    payload_msg = getattr(envelope, field_name)
    for key, value in zip(field_list, params):
        if value is not None:
            setattr(payload_msg, key, value)

    data = envelope.SerializeToString()
    logger.debug(f"[TELEMETRY] SERIALIZED | NAME: {name} | ID={tlm_id} | SIZE={len(data)}B")
    return data

def deserialize_telemetry(payload: bytes) -> dict:
    """
    Deserialize a telemetry payload encoded as protobuf TelemetryEnvelope.
    """
    if not payload:
        raise ValueError("Payload too short")

    tlm_pb = _get_pb()
    envelope = tlm_pb.TelemetryEnvelope()
    envelope.ParseFromString(payload)

    tid = envelope.tlm_id
    which = envelope.WhichOneof("payload")
    
    tlm_fields = _get_tlm_fields()
    
    # Check if this ID exists in our schema-derived field map
    # We look for a field with this number
    field_info = next(((name, info) for name, info in tlm_fields.items() if info[2] == tid), None)

    if not field_info or not which:
        logger.warning(f"[TELEMETRY] Unknown or unmapped telemetry ID: {tid}")
        return {"tlm_id": tid, "raw_payload": payload}

    name, (field_name, field_list, _) = field_info
    msg = getattr(envelope, which)
    fields = {key: getattr(msg, key) for key in field_list}

    logger.debug(
        f"[TELEMETRY] DESERIALIZED | NAME: {name} | ID=0x{tid:02X} | FIELDS={list(fields.keys())}"
    )

    return {"tlm_id": tid, **fields}
