from __future__ import annotations
from collections import namedtuple
import lynk.application.ack.handler.impl as handler
from lynk.application.ack.serializer.dispatcher import serialize_ack, deserialize_ack

AckDefinition = namedtuple("AckDefinition", ["id", "name", "handler", "serialize", "deserialize"])

ack_definitions = {
    0x01: AckDefinition(0x01, "ACK_OK",          handler.ack_ok,          lambda *p: serialize_ack("ACK_OK", *p),          deserialize_ack),
    0x02: AckDefinition(0x02, "ACK_ERROR",       handler.ack_error,       lambda *p: serialize_ack("ACK_ERROR", *p),       deserialize_ack),
    0x03: AckDefinition(0x03, "ACK_BUSY",        handler.ack_busy,        lambda *p: serialize_ack("ACK_BUSY", *p),        deserialize_ack),
    0x04: AckDefinition(0x04, "ACK_INVALID_CMD", handler.ack_invalid_cmd, lambda *p: serialize_ack("ACK_INVALID_CMD", *p), deserialize_ack),
    0x05: AckDefinition(0x05, "ACK_EXECUTION_ERROR", handler.ack_execution_error, lambda *p: serialize_ack("ACK_EXECUTION_ERROR", *p), deserialize_ack),
}