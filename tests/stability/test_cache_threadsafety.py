import pytest
import threading
import time
import random
from lynk.application.telemetry.tools.cache import (
    set_device_data, 
    get_device_data, 
    get_active_device_ids, 
    reset_cache,
    cleanup_stale_data
)

def test_telemetry_cache_thread_safety():
    """
    Stress test for TelemetryCache to ensure no 'dictionary changed size during iteration'
    or data corruption occurs under high concurrent load.
    """
    reset_cache()
    
    NUM_WRITERS = 10
    NUM_READERS = 10
    OPERATIONS_PER_THREAD = 1000
    
    errors = []
    stop_event = threading.Event()

    def writer_thread(tid):
        try:
            for i in range(OPERATIONS_PER_THREAD):
                # Simulate various devices (100-110)
                src_id = 100 + (i % 10)
                set_device_data(src_id, "gps", {"lat": 41.0, "lon": 29.0, "alt": tid}, team_id=1, hop_count=1)
                if i % 100 == 0:
                    time.sleep(0.001) # Yield
        except Exception as e:
            errors.append(f"Writer-{tid}: {e}")

    def reader_thread(tid):
        try:
            for i in range(OPERATIONS_PER_THREAD):
                # Concurrent iteration happens here
                _ = get_active_device_ids(timeout=1.0)
                # Specific read
                _ = get_device_data(100 + (i % 10), "gps")
                if i % 50 == 0:
                    time.sleep(0.001)
        except Exception as e:
            errors.append(f"Reader-{tid}: {e}")

    def cleanup_thread():
        try:
            while not stop_event.is_set():
                # Forcing cleanup while others write/read
                cleanup_stale_data(ttl_seconds=0.1)
                time.sleep(0.01)
        except Exception as e:
            errors.append(f"Cleanup: {e}")

    # Launch threads
    threads = []
    for i in range(NUM_WRITERS):
        t = threading.Thread(target=writer_thread, args=(i,))
        threads.append(t)
    for i in range(NUM_READERS):
        t = threading.Thread(target=reader_thread, args=(i,))
        threads.append(t)
    
    c_thread = threading.Thread(target=cleanup_thread)
    threads.append(c_thread)

    for t in threads:
        t.start()

    # Wait for writers and readers to finish
    for t in threads[:-1]:
        t.join()
    
    stop_event.set()
    c_thread.join()

    # Assertions
    if errors:
        pytest.fail(f"Thread-safety violations detected:\n" + "\n".join(errors))

    print(f"\n[STABILITY TEST] Successfully completed {NUM_WRITERS * OPERATIONS_PER_THREAD} writes and {NUM_READERS * OPERATIONS_PER_THREAD} reads concurrently without errors.")
