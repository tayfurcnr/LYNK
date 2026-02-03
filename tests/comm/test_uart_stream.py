from __future__ import annotations

from src.shared.config import manager as cfg
from src.shared.comm.uart_handler import UARTHandler, IncompleteFrame
from src.core import frame_codec


def _make_handler() -> UARTHandler:
    handler = UARTHandler.__new__(UARTHandler)
    proto = cfg.get_config().get("protocol", {})
    handler.start_byte = proto["start_byte"]
    handler.start_byte_2 = proto["start_byte_2"]
    handler.version = proto["version"]
    return handler


def test_uart_stream_fragmented_frame() -> None:
    cfg.load_config("configs/config.yaml")

    payload = b"hello"
    frame = frame_codec.build_mesh_frame(
        "T", src_id=1, dst_id=0xFF, payload=payload, team_id=1, hop_count=0
    )

    handler = _make_handler()

    chunks = [frame[:3], frame[3:10], frame[10:20], frame[20:35], frame[35:]]
    rx = bytearray()

    parsed = None
    remaining = None
    for chunk in chunks:
        rx.extend(chunk)
        try:
            parsed, remaining = UARTHandler._extract_frame(handler, rx)
            if parsed:
                break
        except IncompleteFrame:
            continue

    assert parsed == frame
    assert remaining == bytearray()
    decoded = frame_codec.parse_mesh_frame(parsed)
    assert decoded["payload"] == payload
