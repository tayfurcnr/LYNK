# 🧭 LYNK Protocol – Guide to Adding a New Command

This document provides a complete guide for developers to **add a new command** to the LYNK communication protocol.

---

## 🎯 Purpose

Ensure that every command:
- Has a unique `command_id` and name
- Is processable through a handler
- Is trackable via the ACK system
- Is testable through automated scripts

---

## 🧩 Step 1 – Define the Command

### File: `src/handlers/command/command_handler.py`

```python
# Register the new command in the dictionary
command_definitions = {
    ...
    0x0A: CommandDefinition("PING", handle_ping),  # ✅ Add your new command here
}
```

> ⚠️ The `command_id` (0x0A) must not conflict with existing IDs.

---

## 🧠 Step 2 – Implement the Command Handler

```python
def handle_ping(cmd_id, params, src_id, interface):
    logger.info("[COMMAND] SENT | CMD: PING")
    send_ack(interface, cmd_id, src_id, True, STATUS_SUCCESS)
```

> ✔️ Perform logic and validation inside the handler. Use `send_ack()` for responses.

---

## ✉️ Step 3 – Create Command Dispatch Function

### File: `src/tools/command/command_dispatcher.py`

```python
def cmd_ping(interface, src: int, dst: int):
    payload = serialize_command(0x0A, b'')  # No parameters
    frame = build_mesh_frame(src_id=src, dst_id=dst, frame_type='C', payload=payload)
    interface.uart.send(frame)
    logger.info(f"[COMMAND] SENT | PING -> DST: {dst}")
```

---

## 📥 Step 4 – Track the ACK Status

ACK responses are automatically handled by `ack_handler.py`.

### File: `src/tools/ack/ack_tracker.py`

```python
status = get_ack_status("PING", dst_id)
if status == 0:
    print("✅ PING successful")
elif status == "EXPIRED":
    print("⚠️ No response (ACK expired)")
else:
    print(f"❌ Failed | Status: {status}")
```

---

## 🧪 Step 5 – Create an Automated Test (Optional but Recommended)

### File: `tests/test_cmd_ping.py`

```python
def test_cmd_ping():
    interface = create_interface()
    start_ack_listener(interface, duration=1.0)
    cmd_ping(interface, src=1, dst=2)
    time.sleep(1)
    assert get_ack_status("PING", 2) == 0
```

---

## 📁 Suggested Directory Structure

```
src/
├── handlers/
│   └── command/
│       └── command_handler.py
├── tools/
│   └── command/
│       ├── command_dispatcher.py
│       └── ack_dispatcher.py
├── serializers/
│   └── command_serializer.py
tests/
└── test_cmd_ping.py
```

---

## ✅ Summary

| Step | Description | File |
|------|-------------|------|
| 🧩 Command Definition | ID, name, and handler | `command_handler.py` |
| 🧠 Command Handler | Execution and ACK | `command_handler.py` |
| ✉️ Dispatch Function | Send command over interface | `command_dispatcher.py` |
| 📥 ACK Tracking | Using `ack_tracker` | `ack_tracker.py` |
| 🧪 Testing | (Optional) Automated test | `tests/` |

---

> For complex commands with parameters (e.g., GIMBAL or WAYPOINTS), extend the handler accordingly using `struct.unpack`.

