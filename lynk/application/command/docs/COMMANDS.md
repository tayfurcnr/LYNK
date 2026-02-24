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
| `0x02` | `SYSTEM_SET_VEHICLE_ID`| `uint32 id, bool persist` | Sets local node identifier (`persist=true` writes config). |
| `0x03` | `SYSTEM_SET_TEAM_ID` | `uint32 team_id, bool persist` | Sets team membership (`persist=true` writes config). |
| `0x15` | `FLIGHT_SET_MODE` | `str mode` | E.g., "GUIDED", "LAND", "AUTO". |
| `0x16` | `FLIGHT_ARMING` | `bool arm` | Arm (1) or Disarm (0) the platform. |
| `0x17` | `FLIGHT_TAKEOFF` | `float alt` | Immediate climb to target altitude. |
| `0x18` | `FLIGHT_GOTO` | `lat, lon, alt` | Navigate to global GPS coordinate. |
| `0x19` | `FLIGHT_SET_SPEED` | `float speed` | Set ground speed in m/s. |
| `0x1E` | `FLIGHT_LAND` | None | Land at current location. |
| `0x29` | `MISSION_UPLOAD` | `JSON` | Upload bulk waypoint or mission data. |
| `0x2A` | `MISSION_CONTROL` | `JSON` | START, PAUSE, or ABORT active mission. |
| `0x51` | `GIMBAL_SET_MODE` | `uint32 mode` | Set gimbal mode (follow/lock/follow_lock). |
| `0x52` | `GIMBAL_SET_ATTITUDE` | `yaw_deg, pitch_deg, roll_deg, speed` | Set target gimbal attitude with speed. |
| `0x53` | `GIMBAL_SET_VELOCITY` | `yaw_rate_dps, pitch_rate_dps, roll_rate_dps` | Continuous gimbal rate control. |
| `0x54` | `GIMBAL_STOP` | None | Emergency stop gimbal motion. |
| `0x55` | `GIMBAL_HOME` | None | Return gimbal to home position. |
| `0x56` | `GIMBAL_TRACK_TARGET_CONTROL` | `enable, video_type, x0, y0, x1, y1` | `enable=true`: start tracking with bbox, `enable=false`: stop tracking. |
| `0x58` | `GIMBAL_SEEK_POSITION` | `target_yaw, target_pitch, target_roll, speed, tolerance` | Seek to target gimbal orientation. |
| `0x59` | `GIMBAL_CALIBRATE` | `uint32 calibration_type` | Trigger gimbal calibration routine. |
| `0x5A` | `CAMERA_TAKE_PHOTO` | None | Capture single photo. |
| `0x5B` | `CAMERA_RECORD_CONTROL` | `bool enable` | `enable=true`: start recording, `enable=false`: stop recording. |
| `0x5D` | `CAMERA_SET_DIGITAL_ZOOM` | `uint32 level` | Set zoom level / incremental zoom command. |
| `0x5E` | `CAMERA_SET_WHITE_BALANCE` | `uint32 mode` | Set RGB white balance mode. |
| `0x5F` | `THERMAL_SET_FALSE_COLOR` | `uint32 palette` | Set thermal false-color palette. |
| `0x60` | `CAMERA_STREAM_CONTROL` | `stream_type, enable` | Start/stop RGB or thermal stream. |
| `0x62` | `GIMBAL_GET_SD_CAPACITY` | None | Query SD capacity (result/event layer integration required). |

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
