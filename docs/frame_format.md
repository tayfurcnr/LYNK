
# 🧱 LYNK Frame Format – Custom Mesh Message Structure

This document explains the custom message frame used in LYNK’s mesh communication system. The frame allows structured communication between UAVs and ground systems, supporting various message types including MAVLink v2, telemetry, commands, and more.

---

## 📐 Frame Structure

| Section | Field         | Size    | Type      | Description |
|--------|---------------|---------|-----------|-------------|
| Header | `start_byte`   | 1 byte  | `uint8_t` | Start byte 1 (default: `0x54`, ASCII 'T') |
|        | `start_byte_2` | 1 byte  | `uint8_t` | Start byte 2 (default: `0xC7`) |
|        | `version`      | 1 byte  | `uint8_t` | Protocol version (default: `0x01`) |
|        | `frame_type`   | 1 byte  | `uint8_t` | Message type (e.g., `0x50` = Ping) |
|        | `team_id`      | 1 byte  | `uint8_t` | Team isolation ID (Frames from other teams are dropped) |
|        | `src_id`       | 1 byte  | `uint8_t` | Source device ID |
|        | `dst_id`       | 1 byte  | `uint8_t` | Destination device ID (`0xFF` = broadcast, `0x00` = team broadcast) |
|        | `payload_len`  | 2 bytes | `uint16_t`| Length of payload (big-endian) |
| Data   | `payload`      | N bytes | `uint8_t[]` | Actual message content |
| CRC    | `crc`          | 2 bytes | `uint16_t`| CRC-16-CCITT-FALSE checksum |

---

## 🧩 Fixed Byte Definitions

| Constant       | Hex   | ASCII | Description |
|----------------|-------|-------|-------------|
| `START_BYTE`   | 0x54  | 'T'   | Start of frame 1 |
| `START_BYTE_2` | 0xC7  | -     | Start of frame 2 |
| `BROADCAST_ID` | 0xFF  | -     | Broadcast to all team nodes |
| `TEAM_BCAST_ID`| 0x00  | -     | Alternative team broadcast ID |

---

## 🧾 Supported Frame Types

| Type Label         | Hex  | ASCII | Purpose |
|--------------------|------|-------|---------|
| MAVLink v2         | 0x4D | 'M'   | Binary MAVLink v2 messages |
| JSON               | 0x4A | 'J'   | JSON-formatted config/state messages |
| Ping               | 0x50 | 'P'   | Latency / connectivity test |
| Ack / Nack         | 0x41 | 'A'   | Command acknowledgment |
| Log / Debug Text   | 0x44 | 'D'   | Logs or text-based diagnostics |
| OTA Firmware Chunk | 0x46 | 'F'   | Firmware update chunks |
| Param Req / Set    | 0x53 | 'S'   | Parameter get/set operations |
| Telemetry Custom   | 0x54 | 'T'   | Non-MAVLink custom telemetry |
| Command            | 0x43 | 'C'   | Command and control binary data |

---

## 🛡️ CRC Validation

All messages are verified using **CRC-16-CCITT-FALSE**. If the CRC does not match, the frame is dropped.

---

## 📣 Notes

- Frame structure is extendable for future message types.
- Frame types are mapped in `frame_router.py` for appropriate dispatching.
