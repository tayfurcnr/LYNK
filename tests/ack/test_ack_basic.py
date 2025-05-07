def test_ack_response_format():
    from src.tools.ack.status_codes import STATUS_LABELS
    assert isinstance(STATUS_LABELS, dict)
    assert 0 in STATUS_LABELS