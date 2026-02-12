import pytest
import time
import threading
import os
import sys

# Ensure proto path is available for imports within proto files
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
proto_dir = os.path.join(root_dir, "lynk/shared/proto")
if proto_dir not in sys.path:
    sys.path.append(proto_dir)

from lynk.application.telemetry.tools.cache import set_device_data, reset_cache
from lynk.application.command.tools.dispatcher import send_command
from lynk.application.ack.tools.tracker import get_ack_tracker

class MockInterface:
    def send(self, data):
        pass

@pytest.fixture(autouse=True)
def setup_config():
    from lynk.shared.config import manager
    manager._config = {
        "vehicle": {
            "id": 1,
            "team_id": 0
        },
        "protocol": {
            "start_byte": 0x24,
            "start_byte_2": 0x24,
            "version": 1
        }
    }
    reset_cache()
    get_ack_tracker().reset()
    yield

def test_team_broadcast_ack():
    interface = MockInterface()
    tracker = get_ack_tracker()
    
    # Node A (Team 1), Node B (Team 2)
    set_device_data(src_id=10, data_type="heartbeat", data={"mode": 1}, team_id=1)
    set_device_data(src_id=20, data_type="heartbeat", data={"mode": 1}, team_id=2)
    
    results_received = {}
    event = threading.Event()

    def callback(results):
        nonlocal results_received
        results_received = results
        event.set()

    # Send command to Team 1
    # SYSTEM_REBOOT maps to ID 1
    send_command(interface, "SYSTEM_REBOOT", dst=0xFF, dst_team_id=1, callback=callback, ack_timeout=2.0, transaction_id="tx-123")
    
    # Simulate ACK from Node A
    time.sleep(0.1)
    tracker.notify_ack(session_id="tx-123", src_id=10, ack_type="ACK_OK")
    
    # Should complete immediately
    assert event.wait(1.0)
    assert 10 in results_received
    assert 20 not in results_received
    assert results_received[10] == "ACK_OK"

def test_global_broadcast_ack():
    interface = MockInterface()
    tracker = get_ack_tracker()
    
    set_device_data(src_id=10, data_type="heartbeat", data={"mode": 1}, team_id=1)
    set_device_data(src_id=20, data_type="heartbeat", data={"mode": 1}, team_id=2)
    
    results_received = {}
    event = threading.Event()

    def callback(results):
        nonlocal results_received
        results_received = results
        event.set()

    # Send global command
    send_command(interface, "SYSTEM_REBOOT", dst=0xFF, dst_team_id=None, callback=callback, ack_timeout=2.0, transaction_id="tx-456")
    
    # Simulate A
    tracker.notify_ack(session_id="tx-456", src_id=10, ack_type="ACK_OK")
    assert not event.wait(0.2) # Should NOT be finished yet
    
    # Simulate B
    tracker.notify_ack(session_id="tx-456", src_id=20, ack_type="ACK_OK")
    assert event.wait(1.0)
    assert 10 in results_received
    assert 20 in results_received
