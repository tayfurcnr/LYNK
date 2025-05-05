# src/serializers/swarm_serializer.py

import struct

def serialize_swarm_command(task_type: int, task_id: int, param_flags: int,
                            start_time: int, p1: float, p2: float, p3: float) -> bytes:
    """
    Swarm görevini baytlara çevirir.
    """
    return struct.pack("<BBBIf f f", task_type, task_id, param_flags, start_time, p1, p2, p3)


def deserialize_swarm_command(payload: bytes) -> dict:
    """
    Swarm görevini bayt dizisinden çözer.
    """
    task_type, task_id, param_flags, start_time, p1, p2, p3 = struct.unpack("<BBBIf f f", payload)
    return {
        "task_type": task_type,
        "task_id": task_id,
        "param_flags": param_flags,
        "start_time": start_time,
        "params": [p1, p2, p3]
    }
