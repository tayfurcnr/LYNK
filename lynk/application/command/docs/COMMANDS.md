# 🎮 Robot Command Center: Reference

The Command module is the primary interface for triggering actions on remote nodes.

## 📡 Protocol Overview
- **Header**: 11-byte V2 standard.
- **Payload**: `[Command ID (1B)][Parameters (NB)]`.
- **Handling**: Managed via `dispatcher.py` (sending) and `handler/impl.py` (receiving).

## 📋 Command Matrix

| ID | Name | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `0x01` | `SYSTEM_REBOOT` | None | Triggers system restart. |
| `0x02` | `SYSTEM_SET_VEHICLE_ID`| `uint32 id` | Sets local node identifier. |
| `0x03` | `SYSTEM_SET_TEAM_ID` | `uint32 team_id` | Sets team membership. |
| `0x15` | `FLIGHT_SET_MODE` | `str mode` | E.g., "GUIDED", "LAND", "AUTO". |
| `0x16` | `FLIGHT_ARMING` | `bool arm` | Arm (1) or Disarm (0) the platform. |
| `0x17` | `FLIGHT_TAKEOFF` | `float alt` | Immediate climb to target altitude. |
| `0x18` | `FLIGHT_GOTO` | `lat, lon, alt` | Navigate to global GPS coordinate. |
| `0x19` | `FLIGHT_SET_SPEED` | `float speed` | Set ground speed in m/s. |
| `0x1E` | `FLIGHT_LAND` | None | Land at current location. |
| `0x29` | `MISSION_UPLOAD` | `JSON` | Upload bulk waypoint or mission data. |
| `0x2A` | `MISSION_CONTROL` | `JSON` | START, PAUSE, or ABORT active mission. |

## 🛠 Extension Procedure

The Command module uses **Protobuf Introspection**. Adding a command follows a schema-first approach:

1.  **Define Schema**: Create a new `.proto` file in `msg/command/` for your command.
2.  **Register Envelope**: Add your message to the `oneof payload` in `msg/command/command_envelope.proto`.
3.  **Generate Code**: Run `python3 setup.py protos` to compile the Python classes.
4.  **Implement Logic (Optional)**: If you need special processing, add a handler function in `handler/impl.py`. **Note**: The function name must match the field name in the Protobuf envelope.
    *   *Tip*: If no specific handler is found, the system uses a **Generic Bridge Handler** that automatically ACKs and prepares the data for ROS forwarding.
5.  **Dispatcher (Optional)**: Add a type-safe wrapper in `tools/dispatcher.py` for easier calling.

> [!TIP]
> Generic sending is supported via `dispatcher.send_command(interface, "COMMAND_NAME", **params)`. This automatically looks up the schema and serializes the data.