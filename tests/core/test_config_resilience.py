import pytest
from src.shared.config import manager

def test_config_safe_defaults():
    """Verify that the config manager returns safe defaults when keys are missing or malformed."""
    
    # Simulate a partial/corrupted config in memory
    # Missing 'udp' sector, missing 'security.key'
    manager._config = {
        "comm_type": "MOCK_UART",
        "node_id": 1,
        "security": {
            "enabled": True
            # 'key' and 'iv' are MISSING
        }
    }
    
    # 1. Test missing top-level sector
    assert manager.get("udp.local_ip", "127.0.0.1") == "127.0.0.1"
    
    # 2. Test missing nested key
    assert manager.get("security.key", "DEFAULT_KEY") == "DEFAULT_KEY"
    
    # 3. Test malformed path (extra dots)
    assert manager.get("comm_type...", "SAFE") == "SAFE"
    
    # 4. Test accessing value as dict (TypeError)
    # comm_type is a string, but we try to access it as a dict
    assert manager.get("comm_type.something", "HANDLED") == "HANDLED"

    print("\n[SUCCESS] Config Resilience verified. Fail-safe defaults returned for missing/malformed keys.")

def test_config_load_invalid_file(tmp_path):
    """Verify that load_config raises appropriate errors for invalid files."""
    invalid_file = tmp_path / "corrupt.yaml"
    invalid_file.write_text("invalid: [unclosed bracket")
    
    with pytest.raises(Exception): # YAML parser will raise error
        manager.load_config(str(invalid_file))
        
    print("[SUCCESS] Invalid config file load handled correctly.")

if __name__ == "__main__":
    pytest.main([__file__])
