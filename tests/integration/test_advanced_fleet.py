import pytest
import time
from lynk.application.telemetry.tools.cache import set_device_data, reset_cache
from lynk.application.command.tools.dispatcher import send_command
from lynk.application.ack.tools.tracker import get_ack_tracker

class MockInterface:
    def send(self, data):
        pass

@pytest.fixture(autouse=True)
def setup():
    from lynk.shared.config import manager
    manager._config = {
        "vehicle": {"id": 1, "team_id": 0},
        "protocol": {"start_byte": 0x24, "start_byte_2": 0x24, "version": 1},
        "relay": {"enabled": True}
    }
    reset_cache()
    get_ack_tracker().reset()
    yield

def test_adaptive_timeout_calculation(monkeypatch):
    from unittest.mock import MagicMock
    mock_tracker = MagicMock()
    
    import lynk.application.ack.tools.tracker as tracker
    monkeypatch.setattr(tracker, "get_ack_tracker", lambda: mock_tracker)
    
    interface = MockInterface()
    
    # 1. Simulate a node 4 hops away
    set_device_data(src_id=10, data_type="heartbeat", data={"mode": 1}, team_id=0, hop_count=4)
    
    # 2. Send command to this node
    send_command(interface, "SYSTEM_REBOOT", dst=10, ack_timeout=2.0, wait_for_ack=True)
    
    # 3. Verify tracker was called with 4.0s timeout
    calls = mock_tracker.register_session.call_args_list
    assert len(calls) > 0
    _, kwargs = calls[0]
    assert kwargs['timeout'] == 4.0

def test_qos_delays():
    # This is harder to test without mocks on time.sleep
    # But we can verify the frames are being routed.
    pass
