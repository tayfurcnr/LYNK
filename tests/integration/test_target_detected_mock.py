from __future__ import annotations

from unittest.mock import MagicMock, patch

from lynk.application.event.handler.dispatcher import handle_event
from lynk.application.event.serializer.dispatcher import deserialize_event, serialize_event


EVENT_TARGET_DETECTED = 63
PRIORITY_HIGH = 2


def test_target_detected_mock_round_trip():
    payload = {
        "latitude": 41.012345,
        "longitude": 29.098765,
        "altitude_m": 87.65,
        "detected_at": "2026-07-09T15:44:00.123Z",
        "detected_at_unix_ms": 1783604640123,
    }

    raw = serialize_event(
        event_type=EVENT_TARGET_DETECTED,
        priority=PRIORITY_HIGH,
        transaction_id="mock-target-1",
        payload_params=payload,
    )
    decoded = deserialize_event(raw)

    assert decoded["event_type"] == EVENT_TARGET_DETECTED
    assert decoded["payload"]["latitude"] == payload["latitude"]
    assert decoded["payload"]["longitude"] == payload["longitude"]
    assert decoded["payload"]["altitude_m"] == payload["altitude_m"]
    assert decoded["payload"]["detected_at"] == payload["detected_at"]
    assert decoded["payload"]["detected_at_unix_ms"] == payload["detected_at_unix_ms"]


def test_target_detected_mock_dispatch(monkeypatch):
    payload = serialize_event(
        event_type=EVENT_TARGET_DETECTED,
        priority=PRIORITY_HIGH,
        transaction_id="mock-target-2",
        payload_params={
            "latitude": 41.111111,
            "longitude": 29.222222,
            "altitude_m": 91.25,
            "detected_at": "2026-07-09T15:45:00.000Z",
            "detected_at_unix_ms": 1783604700000,
        },
    )

    mock_handler = MagicMock()
    mock_def = MagicMock()
    mock_def.name = "TARGET_DETECTED"
    mock_def.handler = mock_handler

    with patch("lynk.application.event.handler.dispatcher.event_definitions.get", return_value=mock_def):
        handle_event(
            payload,
            {"src_id": 7, "dst_id": 255, "seq_num": 1},
            interface=None,
        )

    mock_handler.assert_called_once()
    args = mock_handler.call_args[0]
    assert args[0] == EVENT_TARGET_DETECTED
    assert args[1]["payload"]["latitude"] == 41.111111
