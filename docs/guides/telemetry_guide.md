# Telemetry Extension Guide

## Supported Telemetry Types

The system currently supports the following telemetry types:
- **GPS** (ID: 1) - `lat`, `lon`, `alt`
- **IMU** (ID: 2) - `roll`, `pitch`, `yaw`
- **Battery** (ID: 3) - `voltage`, `current`, `level`
- **Heartbeat** (ID: 4) - `mode`, `health`, `is_armed`, `gps_fix`, `sat_count`
- **Barometer** (ID: 5) - `vertical_speed`, `ground_speed`, `altitude_relative`
- **Ping** (ID: 6) - (Empty, used for presence checks)

## Adding a New Telemetry Type

LYNK uses **Protobuf Introspection** for telemetry. Adding a type is a simple 3-step process:

### 1. Define the Protobuf Message

Create a new `.proto` file in `msg/telemetry/`.

**Example: `msg/telemetry/compass.proto`**
```protobuf
syntax = "proto3";
package lynk.telemetry;

message Compass {
  float heading = 1;
  float declination = 2;
}
```

### 2. Register in the Envelope

Update `msg/telemetry/telemetry_envelope.proto`:

```protobuf
import "msg/telemetry/compass.proto";  // Import your new schema

message TelemetryEnvelope {
  uint32 tlm_id = 255;
  
  oneof payload {
    // ...
    Ping ping = 6;
    Compass compass = 7;  // Assign a unique ID (tag)
  }
}
```

### 3. Compile Protobufs

Run the generation script:
```bash
python3 setup.py protos
```

**That's it!** The system automatically:
- ✅ Generates Serializers/Deserializers
- ✅ Adds to the dynamic Telemetry Registry
- ✅ Maps incoming packets to handlers

## Sending Telemetry

To send the new telemetry, use the generic `send_telemetry` function or add a helper in `tools/dispatcher.py`:

**`lynk/application/telemetry/tools/dispatcher.py`:**
```python
def send_tlm_compass(interface, heading: float, declination: float, dst: int = 0xFF):
    from lynk.application.telemetry.tools.builder import build_tlm_frame
    frame = build_tlm_frame("COMPASS", heading, declination, dst)
    send_frame(interface, frame)
    logger.debug(f"[TELEMETRY] SENT COMPASS | HDG: {heading:.1f}")
```

**Usage:**
```python
import lynk.application.telemetry.tools.dispatcher as tlm
tlm.send_tlm_compass(interface, heading=45.2, declination=1.3)
```

## Receiving Telemetry

Handlers are automatically matched by name. If you need custom processing (e.g., logging or database storage), implement a handler in `lynk/application/telemetry/handler/impl.py`:

**`lynk/application/telemetry/handler/impl.py`:**
```python
def compass(tlm_id, params, src_id, interface):
    heading = params.get("heading", 0.0)
    logger.info(f"[TELEMETRY] RECV | COMPASS | HDG: {heading:.1f}")
    
    # Store in memory cache
    set_device_data(src_id, "compass", params)
```

## Key Concept: Automatic Discovery

- **ID Mapping**: The tag number in `TelemetryEnvelope` determines the protocol ID.
- **Naming**: The handler function name **must** match the field name in the Protobuf envelope.
- **Schema Access**: The system uses `inspect` and `getattr` to link Protobuf messages to logic without hardcoded mapping tables.
