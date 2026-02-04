# 📡 LYNK Protocol v2 Specification

This document defines the binary frame structure for **LYNK Protocol v2**. It is designed for low-overhead, mission-critical aerial and ground robotics communication.

## 🧱 Frame Structure (11-Byte Header)

All fields are Big-Endian (**Network Byte Order**).

| Offset | Field | Size | Details |
| :--- | :--- | :--- | :--- |
| 0 | **Start Byte 1** | 1B | Default: `0x54` (T) |
| 1 | **Start Byte 2** | 1B | Default: `0xC7` (Ç) |
| 2 | **Version** | 1B | Fixed: `0x02` |
| 3 | **Frame Type** | 1B | `T`: Telemetry, `C`: Command, `A`: ACK, `D`: Data |
| 4 | **Team ID** | 1B | `0`: Solo, `1-255`: Teams |
| 5 | **Source ID** | 1B | Unique node ID in the team |
| 6 | **Dest ID** | 1B | `0`: Broadcast, `1-255`: Target node |
| 7 | **Hop Count** | 1B | Decremented by routers. `0` = Drop. |
| 8 | **Flags** | 1B | Bit 0: Compression (1=LZ4), Bit 1-7: Reserved |
| 9 | **Payload Len** | 2B | Length of the data area (N bytes) |
| 11 | **Payload Area**| NB | Encrypted and/or Compressed data |
| 11+N | **CRC16** | 2B | CRC-16-CCITT (False) covering Header + Payload |

## 📦 Features

### 1. LZ4 Compression
If **Flags Bit 0** is set, the Payload Area is compressed using LZ4. Decompression should be performed before processing by logic layers.

### 2. Mesh Routing
The `Hop Count` prevents infinite packet loops. Each "Repeater" node:
1. Checks the `Dest ID`.
2. If it's not the target, decrements `Hop Count`.
3. If `Hop Count > 0`, re-broadcasts the frame.

### 3. Anti-Replay Security
Nodes maintain a `Sequence Manager` per Source ID. If a packet arrives with a `Sequence Number` less than or equal to the last recorded one, it is rejected to prevent replay attacks.

## 🛠️ Implementation Reference
- **Encoder/Decoder**: [src/core/frame_codec.py](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/core/frame_codec.py)
- **UART Extraction**: [src/shared/comm/uart_handler.py](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/shared/comm/uart_handler.py)
