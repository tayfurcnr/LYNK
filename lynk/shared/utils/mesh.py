"""Mesh network utility functions for LYNK protocol."""

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
        
    Raises:
        ValueError: If node_id is negative or window_ms is invalid.
    """
    if node_id < 0:
        raise ValueError(f"node_id must be non-negative, got {node_id}")
    if window_ms <= 0:
        raise ValueError(f"window_ms must be positive, got {window_ms}")
    
    bucket_size = 20 
    slot_index = node_id % bucket_size
    base_delay_ms = slot_index * 10
    remaining_window = window_ms - base_delay_ms
    jitter_ms = random.uniform(0, max(50, remaining_window / 2))
    
    return (base_delay_ms + jitter_ms) / 1000.0

def wait_for_stagger(node_id: int, total_nodes: int = 200, window_ms: int = 500) -> None:
    """
    Utility to block for the staggered duration.
    
    Args:
        node_id: Unique device identifier.
        total_nodes: Expected maximum number of nodes.
        window_ms: Total time window to spread responses over.
        
    Raises:
        ValueError: If parameters are invalid.
    """
    delay = get_staggered_delay(node_id, total_nodes, window_ms)
    time.sleep(delay)
