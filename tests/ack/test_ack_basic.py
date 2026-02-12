def test_ack_response_format():
    from lynk.application.ack.definitions import ack_definitions
    assert isinstance(ack_definitions, dict)
    assert 1 in ack_definitions  # ACK_OK id is 1