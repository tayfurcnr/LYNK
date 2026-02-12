# Compass Telemetry Example

## Adding New Telemetry (Automated System)

This example demonstrates how to add a new **COMPASS** telemetry type using the automated Protobuf system.

### 1. Protobuf Definition

**`msg/telemetry/compass.proto`:**
```protobuf
syntax = "proto3";
package lynk.telemetry;

message Compass {
  float heading = 1;
  float declination = 2;
}
```

### 2. Register in the Envelope

**`msg/telemetry/telemetry_envelope.proto`:**
```protobuf
import "msg/telemetry/compass.proto";

message TelemetryEnvelope {
  uint32 tlm_id = 255;
  
  oneof payload {
    Gps gps = 1;
    Imu imu = 2;
    Battery battery = 3;
    Heartbeat heartbeat = 4;
    Barometer barometer = 5;
    Ping ping = 6;
    Compass compass = 7;  // New entry!
  }
}
```

### 3. Compile

```bash
python3 setup.py protos
```

### 4. Use (Automatic!)

**Sending (Generic Function):**
```python
import lynk.application.telemetry.tools.dispatcher as tlm

# Automatic parameter ordering and validation
tlm.send_telemetry(interface, "COMPASS", heading=45.2, declination=1.3)
```

**Receiving (Automatic Handler):**
No extra code required! The system automatically:
- ✅ Deserializes the telemetry
- ✅ Logs the arrival: `[TELEMETRY] COMPASS received from SRC: 2`
- ✅ Saves to cache: `compass: {heading: 45.2, declination: 1.3}`

### 5. Custom Handler (Optional)

If special logic is needed (e.g., calculations or DB storage), add a handler in `impl.py`:

**`lynk/application/telemetry/handler/impl.py`:**
```python
def compass(data: dict, src_id: int):
    heading = data["heading"]
    declination = data["declination"]
    
    # Custom processing (e.g., calculating true north)
    true_north = heading + declination
    
    set_device_data(src_id, "compass", {
        "heading": heading,
        "declination": declination,
        "true_north": true_north
    })
    
    logger.debug(f"[TELEMETRY] COMPASS | HDG: {heading:.1f}°, TRUE: {true_north:.1f}°")
```

## Comparison

### Old Method (Manual)
1. Create `.proto` file
2. Add to Envelope
3. Compile
4. **Write `send_tlm_compass()` function** ← Manual
5. **Write `compass()` handler** ← Manual

### New Method (Automated)
1. Create `.proto` file
2. Add to Envelope
3. Compile
4. **Just Use It!** ← Automatic

## Advantages

- 🚀 **Rapid Prototyping:** Add new telemetry types in minutes.
- 🔒 **Type Safety:** Protobuf schema validation out of the box.
- 📦 **Automatic Caching:** All telemetry is automatically cached.
- 🪵 **Standard Logging:** Consistent log formats across all types.
- 🔧 **Extensibility:** Easy to add custom handlers when needed.
