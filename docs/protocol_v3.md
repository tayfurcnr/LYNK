# 📡 LYNK Protocol v3 Specification

This document defines the binary frame structure for **LYNK Protocol v3**. It supersedes [protocol v2](protocol_v2.md).

**v3 is a wire-breaking change from v2** — the header layout, CRC placement, and sequence-number location are all different. v2 and v3 nodes cannot interoperate; a fleet must be upgraded together.

## 🧱 Frame Structure (15-Byte Header + Header CRC-8)

All fields are Big-Endian (**Network Byte Order**).

| Offset | Field | Size | Details |
| :--- | :--- | :--- | :--- |
| 0 | **Start Byte 1** | 1B | Default: `0x54` (T) |
| 1 | **Start Byte 2** | 1B | Default: `0xC7` (Ç) |
| 2 | **Version** | 1B | Fixed: `0x03` |
| 3 | **Frame Type** | 1B | `T`: Telemetry, `C`: Command, `A`: ACK, `D`: Data |
| 4 | **Team ID** | 1B | `0`: Solo, `1-255`: Teams |
| 5 | **Source ID** | 1B | Unique node ID in the team |
| 6 | **Dest ID** | 1B | `0`: Broadcast, `1-255`: Target node |
| 7 | **Hop Count** | 1B | Decremented by routers. `0` = Drop. |
| 8 | **Sequence Number** | 4B | Plaintext, anti-replay counter (moved out of the encrypted payload in v3) |
| 12 | **Flags** | 1B | Reserved (compression flag removed in v3) |
| 13 | **Payload Len** | 2B | Length of the data area (N bytes) |
| 15 | **Header CRC-8** | 1B | CRC-8 (poly `0x07`) covering bytes 0–14 — validated before the payload length is ever used to slice the buffer |
| 16 | **Payload Area** | NB | Encrypted data (no compression) |
| 16+N | **Frame CRC-16** | 2B | CRC-16-CCITT (False) covering Header + Header CRC-8 + Payload |

Minimum valid frame size: **18 bytes** (16-byte header incl. CRC-8, 0-byte payload, 2-byte frame CRC-16).

## 📦 What Changed vs. v2

### 1. Header CRC-8 (new)
A corrupted `Payload Len` field can no longer cause an out-of-bounds slice: the header CRC-8 is checked *before* `Payload Len` is used, independently of the frame CRC-16.

### 2. Sequence number moved to the plaintext header (new)
In v2 the sequence number was prepended to the payload before encryption. In v3 it lives in the header, so anti-replay rejection happens **before** decryption is attempted — a replayed frame never reaches the crypto engine.

### 3. LZ4 compression removed
v2's optional LZ4 payload compression has been dropped entirely. The `Flags` byte is reserved; there is no compression bit. `compression_enabled`/`compression_threshold` config keys no longer exist.

### 4. Mesh routing & anti-replay semantics unchanged
Hop-count-based mesh routing and the per-source sequence manager behave the same as in v2 (see [protocol_v2.md](protocol_v2.md#2-mesh-routing)); only the sequence number's position on the wire and the check ordering changed.

## 🛠️ Implementation Reference
- **Encoder/Decoder**: [lynk/core/frame_codec.py](../lynk/core/frame_codec.py)
- **UART Extraction**: [lynk/shared/comm/uart_handler.py](../lynk/shared/comm/uart_handler.py)
