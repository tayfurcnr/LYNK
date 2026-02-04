# 📡 Telemetry Module: Developer Guide

This module handles the processing, serialization, and caching of telemetry data.

## 📁 Structure
- `serializer/dispatcher.py`: Protobuf-based auto-serialization.
- `handler/impl.py`: Core logic for incoming telemetry.
- `definitions.py`: Dynamic registry powered by Protobuf introspection.
- `tools/cache.py`: In-memory storage for the latest device states.

## 🛠 Extending Telemetry
The Telemetry module uses **Protobuf Introspection**. Adding a new type follows these steps:

### 1. Define Schema
Create a `.proto` file in `msg/telemetry/` (e.g., `compass.proto`).

```protobuf
syntax = "proto3";
package lynk.telemetry;

message Compass {
  float heading = 1;
  float declination = 2;
}
```

### 2. Register in Envelope
Add the message to `msg/telemetry/telemetry_envelope.proto`.

```protobuf
import "msg/telemetry/compass.proto";

message TelemetryEnvelope {
  // ...
  oneof payload {
    // ...
    Compass compass = 7;
  }
}
```

### 3. Generate and Implement
1. Run `python3 setup.py protos`.
2. Add a handler in `handler/impl.py` named `compass` (matching the envelope field).
3. (Optional) Add a type-safe sender in `tools/dispatcher.py`.

## 🚀 Usage Tips
- All telemetry handlers update `src.application.telemetry.tools.cache` automatically via `set_device_data`.
- Use `get_device_data(src_id)` to retrieve current state for any node.
- Use `dispatcher.send_telemetry(interface, "COMPASS", heading=45.0, declination=1.2)` for generic sending.