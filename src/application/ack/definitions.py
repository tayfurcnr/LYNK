from __future__ import annotations
from collections import namedtuple
import src.application.ack.handler.impl as handler
import src.application.ack.serializer.impl as codec

AckDefinition = namedtuple("AckDefinition", ["id", "name", "handler", "serialize", "deserialize"])

ack_definitions = {
    0x01: AckDefinition(0x01, "ACK_OK",          handler.ack_ok,          codec.serialize_ack_ok,          codec.deserialize_ack_ok),
    0x02: AckDefinition(0x02, "ACK_ERROR",       handler.ack_error,       codec.serialize_ack_error,       codec.deserialize_ack_error),
    0x03: AckDefinition(0x03, "ACK_BUSY",        handler.ack_busy,        codec.serialize_ack_busy,        codec.deserialize_ack_busy),
    0x04: AckDefinition(0x04, "ACK_INVALID_CMD", handler.ack_invalid_cmd, codec.serialize_ack_invalid_cmd, codec.deserialize_ack_invalid_cmd),
}