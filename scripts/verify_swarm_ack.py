import time
from lynk.application.telemetry.tools.cache import set_device_data, get_active_device_ids
from lynk.application.command.tools.dispatcher import send_command
from lynk.application.ack.tools.tracker import get_ack_tracker
from lynk.shared.log.logger import logger
from lynk.shared.config.manager import load_config

# Mock interface
class MockInterface:
    def send(self, data):
        pass

def test_swarm_ack():
    # Manual mock config setup
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
    
    interface = MockInterface()
    tracker = get_ack_tracker()
    
    # 1. Setup mock telemetry
    logger.info("Setting up mock topology: Node A (Team 1), Node B (Team 2)")
    set_device_data(src_id=10, data_type="state", data={"mode": 1}, team_id=1)
    set_device_data(src_id=20, data_type="state", data={"mode": 1}, team_id=2)
    
    def on_ack_received(results):
        logger.info(f"CALLBACK RECEIVED: {results}")

    # 2. Test Team 1 Broadcast
    logger.info("--- TEST 1: Team 1 Broadcast ---")
    send_command(interface, "SYSTEM_REBOOT", dst=0xFF, dst_team_id=1, callback=on_ack_received, ack_timeout=5.0)
    
    # 3. Test Global Broadcast
    logger.info("--- TEST 2: Global Broadcast ---")
    send_command(interface, "SYSTEM_REBOOT", dst=0xFF, dst_team_id=None, callback=on_ack_received, ack_timeout=5.0)

if __name__ == "__main__":
    test_swarm_ack()
