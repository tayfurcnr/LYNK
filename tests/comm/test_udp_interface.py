import pytest
import time
import socket
from src.shared.comm.udp_handler import UDPHandler
from src.shared.config import manager

def test_udp_handler_loopback():
    """Verify that UDPHandler can send and receive packets on loopback."""
    
    # 1. Setup mock config for loopback
    manager._config = {
        "udp": {
            "local_ip": "127.0.0.1",
            "local_port": 5005,
            "remote_ip": "127.0.0.1",
            "remote_port": 5005,
            "window_sec": 1.0,
            "max_window_bytes": 1000000,
            "rcvbuf_bytes": 1024 * 1024,
            "idle_sleep_sec": 0.001
        }
    }
    
    handler = UDPHandler()
    handler.start()
    
    try:
        # 2. Send a test packet
        test_data = b"HELLO_UDP_TEST"
        handler.send(test_data)
        
        # 3. Wait for reception (worker thread is running)
        timeout = 2.0
        start_time = time.time()
        received = None
        
        while time.time() - start_time < timeout:
            received = handler.read()
            if received:
                break
            time.sleep(0.1)
            
        assert received == test_data, f"Expected {test_data}, got {received}"
        
        # 4. Test windowed reading
        window_data = handler.read_window(seconds=1.0)
        assert len(window_data) >= 1
        assert window_data[0] == test_data
        
    finally:
        handler.stop()

def test_udp_handler_window_expiry():
    """Verify that packets expire from the time window."""
    manager._config = {
        "udp": {
            "local_ip": "127.0.0.1", "local_port": 5006,
            "remote_ip": "127.0.0.1", "remote_port": 5006,
            "window_sec": 0.5, # Short window
            "max_window_bytes": 1000000
        }
    }
    
    handler = UDPHandler()
    handler._enqueue_latest(b"OLD_PACKET")
    
    # Check it exists
    assert len(handler.read_window()) == 1
    
    # Wait for expiry
    time.sleep(0.6)
    
    # Prune should happen during read
    assert len(handler.read_window()) == 0
    
    handler.stop()

if __name__ == "__main__":
    pytest.main([__file__])
