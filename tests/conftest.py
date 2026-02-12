import os
import pytest
from lynk.shared.config.manager import load_config
import lynk.shared.config.manager as cfg_manager

@pytest.fixture(scope="session", autouse=True)
def setup_config():
    import sys
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proto_dir = os.path.join(root_dir, "lynk/shared/proto")
    if proto_dir not in sys.path:
        sys.path.insert(0, proto_dir)
    
    config_path = os.path.join(root_dir, "configs/config.yaml")
    
    # Load config
    load_config(config_path)
    
    # Override interface for testing in memory
    cfg_manager._config["interface"]["comm_type"] = "MOCK_UART"
    
    return cfg_manager._config

@pytest.fixture(autouse=True)
def reset_singletons():
    from lynk.core.sequence_manager import get_sequence_manager
    from lynk.application.telemetry.tools.cache import reset_cache
    from lynk.application.ack.tools.tracker import get_ack_tracker
    
    get_sequence_manager()._in_seq_map.clear()
    get_sequence_manager()._out_seq = 0
    reset_cache()
    get_ack_tracker().reset()
    yield
