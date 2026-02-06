import pytest
from src.core.sequence_manager import get_sequence_manager

def test_sequence_number_rollover_logic():
    """
    Verifies that the SequenceManager correctly handles 32-bit rollover
    using circular comparison.
    """
    sm = get_sequence_manager()
    sm._in_seq_map.clear()
    
    src_id = 99
    
    # 1. Start near the end of 32-bit range
    # 0xFFFFFFFF = 4,294,967,295
    MAX_32 = 0xFFFFFFFF
    sm.verify_in_seq(src_id, MAX_32 - 1) # Set baseline
    
    # 2. Sequential increase should pass
    assert sm.verify_in_seq(src_id, MAX_32) == True
    
    # 3. Rollover to 0 should pass (Special case for sync or wrap)
    assert sm.verify_in_seq(src_id, 0) == True
    
    # 4. Small number after rollover should pass
    assert sm.verify_in_seq(src_id, 5) == True
    
    # 5. Old number from before rollover should FAIL (Replay protection)
    assert sm.verify_in_seq(src_id, MAX_32 - 10) == False
    
    # 6. Verify "Forward Window" (2^31)
    # Reset to a known state (e.g., 5)
    sm._in_seq_map[src_id] = 5
    
    # 2^31 - 1 forward should pass
    forward_max = (5 + 0x7FFFFFFF) & 0xFFFFFFFF
    assert sm.verify_in_seq(src_id, forward_max) == True
    
    # 7. Beyond forward window should fail
    # Reset back to 5 to test a single HUGE jump from 5
    sm._in_seq_map[src_id] = 5
    too_far = (5 + 0x80000000) & 0xFFFFFFFF
    assert sm.verify_in_seq(src_id, too_far) == False

def test_sequence_out_wrap():
    """Verifies outgoing sequence also wraps correctly at 32-bit."""
    sm = get_sequence_manager()
    sm._out_seq = 0xFFFFFFFF
    
    next_seq = sm.get_next_out_seq()
    # Should wrap to 0 (or 1 depending on implementation, but must be within 32-bit)
    assert next_seq <= 0xFFFFFFFF
    assert next_seq < 0xFFFFFFFF 
