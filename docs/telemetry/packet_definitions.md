# 📡 LYNK Telemetry Packet Definitions

This document details the structure, data types, and sizes of the telemetry packets currently used in the LYNK system.

| ID | Name | Data Fields | Types | Total Size (Bytes) |
| :--- | :--- | :--- | :--- | :--- |
| **0x01** | **GPS** | `lat`, `lon`, `alt` | 3 x `float32` | 12 |
| **0x02** | **IMU** | `roll`, `pitch`, `yaw` | 3 x `float32` | 12 |
| **0x03** | **BATTERY** | `voltage`, `current`, `level` | 3 x `float32` | 12 |
| **0x04** | **HEARTBEAT**| `mode`, `health`, `is_armed`, `gps_fix`, `sat_count` | 2 x `str[32]`, 2 x `bool`, 1 x `uint8` | 67 |
| **0x05** | **BAROMETER**| `vertical_speed`, `ground_speed`, `altitude_relative` | 3 x `float32` | 12 |
| **0x06** | **PING** | `sequence` | 1 x `uint32` | 4 |

---

## 🛠 Serialization Details
- **Endianness**: Big-Endian (`>`)
- **Float Format**: IEEE 754 precision
- **String Handling**: Fixed 32-byte width, null-padded (`\x00`)
