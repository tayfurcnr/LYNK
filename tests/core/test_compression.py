import sys
import os
import pytest
import lz4.block

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from lynk.core.frame_codec import build_mesh_frame, parse_mesh_frame, FLAG_COMPRESSED
from lynk.shared.config.manager import get_config, load_config

# Load default config for tests
load_config(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../configs/config.yaml')))

def test_compression_small_payload():
    """Verify that small payloads are NOT compressed."""
    payload = b"small payload"
    frame = build_mesh_frame('T', 1, 2, payload)
    parsed = parse_mesh_frame(frame)
    
    assert parsed["payload"] == payload
    assert not (parsed["flags"] & FLAG_COMPRESSED)

def test_compression_large_compressible_payload():
    """Verify that large compressible payloads ARE compressed."""
    # 200 bytes of highly repetitive data (very compressible)
    payload = b"A" * 200
    frame = build_mesh_frame('T', 1, 2, payload)
    parsed = parse_mesh_frame(frame)
    
    assert parsed["payload"] == payload
    assert parsed["flags"] & FLAG_COMPRESSED
    
    # Verify wire size is smaller than header + seq + encrypted_orig
    # Header 11 + Payload + CRC 2 = 13 + payload_len
    # Original would be 13 + (4 seq + 200 payload) = 217 (assuming no encryption overhead)
    # Compressed should be much smaller
    assert len(frame) < 100 

def test_compression_large_incompressible_payload():
    """Verify that large UNcompressible payloads are NOT compressed."""
    # 200 bytes of random data (incompressible)
    payload = os.urandom(200)
    frame = build_mesh_frame('T', 1, 2, payload)
    parsed = parse_mesh_frame(frame)
    
    assert parsed["payload"] == payload
    assert not (parsed["flags"] & FLAG_COMPRESSED)
    assert len(frame) > 200

def test_compression_disabled_via_config():
    """Verify that compression can be disabled in config."""
    cfg = get_config()
    orig_enabled = cfg["protocol"].get("compression_enabled", True)
    
    try:
        cfg["protocol"]["compression_enabled"] = False
        payload = b"A" * 200
        frame = build_mesh_frame('T', 1, 2, payload)
        parsed = parse_mesh_frame(frame)
        
        assert parsed["payload"] == payload
        assert not (parsed["flags"] & FLAG_COMPRESSED)
    finally:
        cfg["protocol"]["compression_enabled"] = orig_enabled

def test_compression_threshold_config():
    """Verify that compression threshold is respected."""
    cfg = get_config()
    orig_threshold = cfg["protocol"].get("compression_threshold", 128)
    
    try:
        # Set threshold high
        cfg["protocol"]["compression_threshold"] = 500
        payload = b"A" * 200 # Smaller than 500
        frame = build_mesh_frame('T', 1, 2, payload)
        parsed = parse_mesh_frame(frame)
        assert not (parsed["flags"] & FLAG_COMPRESSED)
        
        # Set threshold low
        cfg["protocol"]["compression_threshold"] = 50
        frame = build_mesh_frame('T', 1, 2, payload)
        parsed = parse_mesh_frame(frame)
        assert parsed["flags"] & FLAG_COMPRESSED
    finally:
        cfg["protocol"]["compression_threshold"] = orig_threshold

if __name__ == "__main__":
    pytest.main([__file__])
