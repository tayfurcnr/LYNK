# Changelog

## Protocol v3 (breaking)

**Wire-incompatible with v2 — the whole fleet (vehicles + GCS) must upgrade together, not in a rolling fashion.**

- **New header CRC-8**: the 15-byte header now carries its own CRC-8 (byte 15), checked before `Payload Len` is used to slice the buffer. Catches header corruption independently of the frame CRC-16.
- **Sequence number moved to the plaintext header**: previously prepended to the payload before encryption; now a 4-byte field in the header. Anti-replay rejection happens *before* decryption is attempted.
- **LZ4 compression removed**: the `Flags` compression bit, `compression_enabled`/`compression_threshold` config keys, `lz4` dependency, and `tools/compression_demo.py` are all gone.
- **Protocol version is config-driven again**: `load_protocol_config()` reads `protocol.version` from config instead of hardcoding it; all shipped config templates bump `version: 2` → `3`.
- Frame size: 15-byte header + 1-byte header CRC-8 + payload + 2-byte frame CRC-16 (was 11-byte header + payload + 2-byte CRC in v2). Minimum frame size is now 18 bytes (was 13).

See [docs/protocol_v3.md](docs/protocol_v3.md) for the full frame layout, and [docs/protocol_v2.md](docs/protocol_v2.md) for the superseded v2 spec.
