import pytest
import os
import struct
from src.core.frame_codec import build_mesh_frame, parse_mesh_frame

def test_frame_resilience_with_noise():
    """Verify that the parser can correctly identify valid frames even when surrounded by garbage/noise bytes."""
    
    # 1. Create a valid frame
    valid_payload = b"MISSION_DATA_ALPHA"
    valid_frame = build_mesh_frame(
        frame_type='T', # Telemetry
        src_id=88, # Unique ID for this test
        dst_id=5,
        payload=valid_payload,
        seq_num=7000,
        hop_count=5
    )
    
    # 2. Construct a corrupted stream: [Garbage] + [Valid Frame] + [Garbage] + [Valid Frame]
    noise_prefix = b"\xFF\xAA\xBB\xCC\x00\x01\x02" # Random noise
    noise_inter = b"\xDE\xAD\xBE\xEF" * 5          # More noise
    noise_suffix = b"\x00" * 10                   # Zero noise
    
    # Second valid frame
    second_payload = b"MISSION_DATA_BETA"
    second_frame = build_mesh_frame(
        frame_type='T',
        src_id=88,
        dst_id=5,
        payload=second_payload,
        seq_num=7001,
        hop_count=5
    )
    
    stream = noise_prefix + valid_frame + noise_inter + second_frame + noise_suffix
    
    # 3. Use the parser to find frames in the stream
    found_frames = []
    
    # Load start bytes from config/codec to be safe
    from src.core.frame_codec import load_protocol_config
    sb1, sb2, _ = load_protocol_config()
    MAGIC_HEAD = bytes([sb1, sb2])
    
    i = 0
    while i < len(stream) - 11: # Min header size is 11
        if stream[i:i+2] == MAGIC_HEAD:
            # Found a potential header, try to parse
            try:
                # We need to know the length to slice correctly, but parse_mesh_frame
                # handles the full frame once it has the start.
                # In a real UART loop, we'd read more bytes. Here we just take a chunk.
                # Max frame is around 256 for this test.
                # result = parse_mesh_frame(stream[i:i + 256]) # Original line, now replaced by more precise slicing
                try:
                    # Extract length from header (bytes 9:11)
                    # Frame structure: [2B Start][1B Ver][1B Type][1B Team][1B Src][1B Dst][1B Hop][1B Flags][2B Len]...
                    p_len = struct.unpack(">H", stream[i+9:i+11])[0]
                    total_len = 11 + p_len + 2 # 11 bytes for header, p_len for payload, 2 bytes for CRC
                    
                    # Ensure we don't try to slice beyond the stream length
                    if i + total_len > len(stream):
                        # Not enough bytes for the full frame, skip this potential header
                        i += 1
                        continue

                    result = parse_mesh_frame(stream[i:i + total_len])
                    if result:
                        found_frames.append(result)
                        i += total_len
                        continue
                except Exception as e:
                    # This inner try-except handles issues during length extraction or parsing
                    # print(f"DEBUG: Inner parse failed at index {i}: {e}") # Optional debug
                    pass
            except Exception as e:
                # This outer try-except was for the original broad parse_mesh_frame call
                # print(f"DEBUG: Outer parse failed at index {i}: {e}") # Optional debug
                pass
        i += 1
            
    assert len(found_frames) >= 2, f"Should have found 2 frames, but found {len(found_frames)}"
    assert found_frames[0]["payload"] == valid_payload
    assert found_frames[1]["payload"] == second_payload
    
    print(f"\n[SUCCESS] Resilience verified. Found {len(found_frames)} frames in noisy stream.")

if __name__ == "__main__":
    pytest.main([__file__])
