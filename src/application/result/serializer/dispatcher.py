from __future__ import annotations
# src/application/result/serializer/dispatcher.py

from typing import Optional
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
        from src.shared.proto.msg.result import result_envelope_pb2 as res_pb
        _PB = res_pb
        return _PB
    except Exception as exc:
        raise RuntimeError(
            "Result protobuf modules not found or invalid. Run 'python3 setup.py protos' first."
        ) from exc


def serialize_result(
    tx_id: str,
    status: str,
    error_code: Optional[int] = None,
    message: Optional[str] = None
) -> bytes:
    """
    Serialize command result payload.

    status: "SUCCESS" | "FAILURE" | "TIMEOUT"
    """
    res_pb = _get_pb()
    envelope = res_pb.ResultEnvelope()
    envelope.tx_id = tx_id
    payload = envelope.result
    payload.SetInParent()

    status_upper = status.upper()
    if status_upper not in ("SUCCESS", "FAILURE", "TIMEOUT"):
        raise ValueError(f"Invalid status: {status}")
    payload.status = getattr(res_pb.CommandResult, status_upper)

    if error_code is not None:
        payload.error_code = int(error_code)
    if message:
        payload.message = message

    data = envelope.SerializeToString()
    logger.debug(f"[RESULT] SERIALIZED | STATUS: {status_upper} | TX_ID: {tx_id} | SIZE={len(data)}B")
    return data


def deserialize_result(payload: bytes) -> dict:
    """
    Deserialize result payload.
    """
    if not payload:
        raise ValueError("Payload too short")

    res_pb = _get_pb()
    envelope = res_pb.ResultEnvelope()
    envelope.ParseFromString(payload)

    tx_id = envelope.tx_id
    which = envelope.WhichOneof("payload")
    if not which:
        raise ValueError("Result payload missing")

    msg = getattr(envelope, which)
    status_name = res_pb.CommandResult.Status.Name(msg.status)
    data = {
        "tx_id": tx_id,
        "status": status_name,
    }
    if msg.error_code:
        data["error_code"] = msg.error_code
    if msg.message:
        data["message"] = msg.message

    logger.debug(f"[RESULT] DESERIALIZED | STATUS: {status_name} | TX_ID: {tx_id}")
    return data
