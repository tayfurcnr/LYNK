# 📡 LYNK – Adding a New Telemetry Type (e.g., HEARTBEAT)

This guide explains how to add a new telemetry data type to the LYNK communication system. We use the example of `HEARTBEAT` telemetry, which includes status fields like flight mode, GPS fix, and arming state.

---

## 🧱 Step 1: Register Telemetry ID

Define a new telemetry type ID in the telemetry protocol. For example:

```python
# src/serializers/telemetry/telemetry_type_constants.py
TELEMETRY_TYPE_IDS = {
    "GPS": 0x01,
    "IMU": 0x02,
    "BATTERY": 0x03,
    "HEARTBEAT": 0x04  # ✅ Add this
}
```

---

## 📦 Step 2: Define Serialization Logic

Update the codec mapping used for binary packing/unpacking of telemetry frames:

```python
# src/serializers/telemetry_serializer.py

TELEMETRY_CODECS = {
    0x04: {  # HEARTBEAT
        "serialize": lambda *p: (
            p[0].encode("utf-8")[:32].ljust(32, b'\x00') +
            p[1].encode("utf-8")[:32].ljust(32, b'\x00') +
            struct.pack(">??Bf", *p[2:])
        ),
        "deserialize": lambda data: {
            "mode": data[:32].decode("utf-8").rstrip('\x00'),
            "health": data[32:64].decode("utf-8").rstrip('\x00'),
            **dict(zip(
                ["is_armed", "gps_fix", "sat_count", "timestamp"],
                struct.unpack(">??Bf", data[64:])
            ))
        }
    },
    ...
}
```

---

## 🧪 Step 3: Add Telemetry Builder

Add a `build_tlm_heartbeat()` function to package the data:

```python
# src/tools/telemetry/telemetry_builder.py

def build_tlm_heartbeat(mode, health, is_armed, gps_fix, sat_count, dst=0xFF, src=None):
    return build_tlm_frame(0x04, [mode, health, is_armed, gps_fix, sat_count], dst, src)
```

---

## 📤 Step 4: Add Dispatcher Function

Create a sender function that uses the builder:

```python
# src/tools/telemetry/telemetry_dispatcher.py

def send_tlm_heartbeat(interface, mode, health, is_armed, gps_fix, sat_count, dst=0xFF, src=None):
    frame = build_tlm_heartbeat(mode, health, is_armed, gps_fix, sat_count, dst, src)
    send_frame(interface, frame)
    logger.info(f"[TELEMETRY] SENT | HEARTBEAT -> DST: {dst} | MODE: {mode}, HEALTH: {health}, ARMED: {is_armed}, FIX: {gps_fix}, SATS: {sat_count}")
```

---

## 🔁 Step 5: Update Handler Logic

Update `handle_telemetry()` to process and cache the new type:

```python
# src/handlers/telemetry/telemetry_handler.py

TELEMETRY_TYPE_MAP = {
    0x01: "gps",
    0x02: "imu",
    0x03: "battery",
    0x04: "heartbeat"  # ✅ Add this
}

def handle_heartbeat_data(data, src_id, data_type):
    heartbeat_data = {
        "mode": data["mode"],
        "health": data["health"],
        "is_armed": data["is_armed"],
        "gps_fix": data["gps_fix"],
        "sat_count": data["sat_count"]
    }
    set_device_data(src_id, data_type, heartbeat_data)
    logger.info(f"[TELEMETRY] Received HEARTBEAT from SRC: {src_id}")
    logger.debug(f"[TELEMETRY] -> MODE: {data['mode']}, HEALTH: {data['health']}, ARMED: {data['is_armed']}, GPS_FIX: {data['gps_fix']}, SATS: {data['sat_count']}")
```

Then add dispatch logic:

```python
if data_type == "heartbeat":
    handle_heartbeat_data(data, src_id, data_type)
```

---

## ✅ Step 6: Test Integration

Use `send_tlm_heartbeat()` in your test:

```python
send_tlm_heartbeat(interface, mode="GUIDED", health="OK", is_armed=True, gps_fix=True, sat_count=10, dst=1, src=1)
```

Verify it's stored in the telemetry cache:

```python
heartbeat_data = get_device_data(1, "heartbeat")
assert heartbeat_data["mode"] == "GUIDED"
```

---

## 🎉 Done!

Your new telemetry type is now integrated with:
- Serialization & deserialization
- Frame building and dispatching
- Caching and test validation
