import pytest
import time
import threading
import os
import sys

# Ensure proto path is available
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
proto_dir = os.path.join(root_dir, "lynk/shared/proto")
if proto_dir not in sys.path:
    sys.path.append(proto_dir)

from lynk.application.telemetry.tools.cache import set_device_data, reset_cache
from lynk.application.command.tools.dispatcher import send_command
from lynk.application.ack.tools.tracker import get_ack_tracker
from lynk.core.frame_codec import parse_mesh_frame
from lynk.application.command.serializer.dispatcher import deserialize_command

class MockInterface:
    def __init__(self):
        self.sent_frames = []
    def send(self, data):
        self.sent_frames.append(data)

@pytest.fixture(autouse=True)
def setup():
    from lynk.shared.config import manager
    manager._config = {
        "vehicle": {"id": 1, "team_id": 0},
        "protocol": {"start_byte": 0x24, "start_byte_2": 0x24, "version": 1}
    }
    reset_cache()
    get_ack_tracker().reset()
    yield

def test_smart_retry_logic():
    interface = MockInterface()
    tracker = get_ack_tracker()
    
    # Node A (10), Node B (20)
    set_device_data(src_id=10, data_type="state", data={"mode": 1}, team_id=1)
    set_device_data(src_id=20, data_type="state", data={"mode": 1}, team_id=1)
    
    results_received = {}
    event = threading.Event()

    def callback(results):
        nonlocal results_received
        results_received = results
        event.set()

    # Send command with 1 retry, 1s timeout, 1s interval
    send_command(interface, "SYSTEM_REBOOT", dst=0xFF, callback=callback, ack_timeout=1.0, max_retries=1, retry_interval=1.0)
    
    # 1. First attempt: Broadcast
    assert len(interface.sent_frames) == 1
    
    # Extract transaction_id from sent frame
    first_frame = parse_mesh_frame(interface.sent_frames[0])
    cmd_data = deserialize_command(first_frame["payload"])
    tx_id = cmd_data["transaction_id"]
    
    # Node A ACKs immediately
    tracker.notify_ack(session_id=tx_id, src_id=10, ack_type="ACK_OK")
    
    # Wait for first timeout (1s)
    time.sleep(1.2)
    
    # 2. After timeout, should see a second attempt (Unicast to Node B)
    # interface.sent_frames should now have 2 frames
    assert len(interface.sent_frames) == 2
    
    # Check if second frame is unicast to 20
    last_frame_raw = interface.sent_frames[-1]
    parsed = parse_mesh_frame(last_frame_raw)
    assert parsed["dst_id"] == 20
    
    # Now Node B ACKs
    tracker.notify_ack(session_id=tx_id, src_id=20, ack_type="ACK_OK")
    
    # Callback should trigger shortly
    assert event.wait(1.0)
    assert results_received[10] == "ACK_OK"
    assert results_received[20] == "ACK_OK"
    assert len(results_received) == 2
