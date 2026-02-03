import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.sequence_manager import SequenceManager
import struct

def test_sequence_protection():
    manager = SequenceManager()
    src_id = 5
    
    print(f"Testing Sequence Protection for SRC_ID: {src_id}")
    
    # 1. Test normal increment
    seq1 = 10
    assert manager.verify_in_seq(src_id, seq1) == True, "Should accept first sequence"
    print(f"Accepted sequence: {seq1}")
    
    seq2 = 11
    assert manager.verify_in_seq(src_id, seq2) == True, "Should accept higher sequence"
    print(f"Accepted sequence: {seq2}")
    
    # 2. Test Replay (Same sequence)
    assert manager.verify_in_seq(src_id, seq2) == False, "REPLAY DETECTED: Should reject same sequence"
    print(f"Correctly rejected replay of sequence: {seq2}")
    
    # 3. Test Old Sequence (Lower)
    seq3 = 5
    assert manager.verify_in_seq(src_id, seq3) == False, "REPLAY DETECTED: Should reject lower sequence"
    print(f"Correctly rejected old sequence: {seq3}")
    
    # 4. Test Wrap-around / Reset (Sequence 0)
    # Allowing 0 as a special case for initial sync or system reset
    assert manager.verify_in_seq(src_id, 0) == True, "Should allow sequence 0 for reset/sync"
    print("Accepted sequence 0 (Sync/Reset)")
    
    # 5. Outgoing sequence test
    out1 = manager.get_next_out_seq()
    out2 = manager.get_next_out_seq()
    print(f"Outgoing sequences: {out1}, {out2}")
    assert out2 == out1 + 1, "Outgoing sequences should increment"

    print("\nSUCCESS: Anti-Replay protection verified.")

if __name__ == "__main__":
    test_sequence_protection()
