# 📡 LYNK – Adding a New Telemetry Type

This guide explains how to add a new telemetry data type to the LYNK communication system using the current modular structure.

---

## 🧱 Step 1: Define ID and Mapping

Register the new telemetry type in the central definitions file. This maps the ID to its name, handler, and serialization functions.

```python
# lynk/application/telemetry/definitions.py

telemetry_definitions = {
    ...
    0x07: TelemetryDefinition(0x07, "NEW_TYPE", handler.new_type, codec.serialize_new_type, codec.deserialize_new_type),
}
```

---

## 📦 Step 2: Implement Serialization

Add the binary pack/unpack logic to the telemetry serializer implementation.

```python
# lynk/application/telemetry/serializer/impl.py

def serialize_new_type(param1: float, param2: int) -> bytes:
    return struct.pack(">fI", param1, param2)

def deserialize_new_type(data: bytes) -> dict:
    param1, param2 = struct.unpack(">fI", data)
    return {"param1": param1, "param2": param2}
```

---

## 🔁 Step 3: Implement Handling logic

Define how the incoming data should be processed and stored in the cache.

```python
# lynk/application/telemetry/handler/impl.py

def new_type(data: dict, src_id: int):
    processed_data = {
        "p1": data["param1"],
        "p2": data["param2"]
    }
    set_device_data(src_id, "new_type", processed_data)
    logger.info(f"[TELEMETRY] NEW_TYPE received from SRC: {src_id}")
```

---

## 📤 Step 4: Add Tools (Optional)

Add high-level tools to easily send or build the new telemetry frame.

```python
# lynk/application/telemetry/tools/dispatcher.py

def send_tlm_new_type(interface, p1, p2, dst=0xFF, src=None):
    # Uses build_tlm_frame internally with ID 0x07
    ...
```

---

## ✅ Step 5: Test Integration

You can now use your new telemetry type in `main.py` or automated tests.

```python
tlm.send_tlm_new_type(interface, p1=1.2, p2=42, dst=0, src=my_id)
```

---

## 🎉 Done!
The system will automatically route, deserialize, and handle the new telemetry type based on the `telemetry_definitions` registry.
