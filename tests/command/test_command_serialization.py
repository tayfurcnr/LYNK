from __future__ import annotations
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/shared/proto')))

from src.application.command.serializer.dispatcher import serialize_command, deserialize_command

def test_serialize_command():
    # 0x03 is SYSTEM_SET_TEAM_ID, expects team_id
    params = {"team_id": 100}
    frame = serialize_command(0x03, params)
    
    result = deserialize_command(frame)
    
    assert result["command_id"] == 0x03
    assert result["params"]["team_id"] == 100