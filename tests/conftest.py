import os
import pytest
from src.shared.config.manager import load_config
import src.shared.config.manager as cfg_manager

@pytest.fixture(scope="session", autouse=True)
def setup_config():
    import sys
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    proto_dir = os.path.join(root_dir, "src/shared/proto")
    if proto_dir not in sys.path:
        sys.path.insert(0, proto_dir)
    
    config_path = os.path.join(root_dir, "configs/config.yaml")
    
    # Load config
    load_config(config_path)
    
    # Override interface for testing in memory
    cfg_manager._config["interface"]["comm_type"] = "MOCK_UART"
    
    return cfg_manager._config
