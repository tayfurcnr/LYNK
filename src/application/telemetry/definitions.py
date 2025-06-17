from collections import namedtuple
import src.application.telemetry.handler.impl as handler
import src.application.telemetry.serializer.impl as codec

TelemetryDefinition = namedtuple("TelemetryDefinition", ["id", "name", "handler", "serialize", "deserialize"])

telemetry_definitions = {
    0x01: TelemetryDefinition(0x01, "GPS",       handler.gps,       codec.serialize_gps,       codec.deserialize_gps),
    0x02: TelemetryDefinition(0x02, "IMU",       handler.imu,       codec.serialize_imu,       codec.deserialize_imu),
    0x03: TelemetryDefinition(0x03, "BATTERY",   handler.battery,   codec.serialize_battery,   codec.deserialize_battery),
    0x04: TelemetryDefinition(0x04, "HEARTBEAT", handler.heartbeat, codec.serialize_heartbeat, codec.deserialize_heartbeat),
}
