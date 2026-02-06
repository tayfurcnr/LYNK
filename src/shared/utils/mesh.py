import random
import time

def get_staggered_delay(node_id: int, total_nodes: int = 200, window_ms: int = 500) -> float:
    """
    Calculates a staggered delay to avoid ACK collisions in large swarms.
    Uses a hybrid approach: ID-based grouping + local randomization.
    
    Args:
        node_id: Unique device identifier.
        total_nodes: Expected maximum number of nodes.
        window_ms: Total time window to spread responses over (default 500ms).
        
    Returns:
        float: Delay in seconds.
    """
    # Group nodes into buckets of 20 to keep slots clean
    # For node_id=200, this naturally wraps but spreads well
    bucket_size = 20 
    slot_index = node_id % bucket_size
    
    # Base delay based on slot (e.g., 0ms, 10ms, 20ms...)
    # Even for 200 nodes, max base delay is only (19 * 10) = 190ms
    base_delay_ms = slot_index * 10
    
    # Add significant random jitter within the remaining window
    # This prevents nodes in the same "slot index" from clashing
    remaining_window = window_ms - base_delay_ms
    jitter_ms = random.uniform(0, max(50, remaining_window / 2))
    
    return (base_delay_ms + jitter_ms) / 1000.0

def wait_for_stagger(node_id: int, total_nodes: int = 200, window_ms: int = 500):
    """Utility to block for the staggered duration."""
    delay = get_staggered_delay(node_id, total_nodes, window_ms)
    time.sleep(delay)
