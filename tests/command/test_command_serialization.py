def test_serialize_command():
    from src.serializers.command_serializer import serialize_command, deserialize_command
    frame = serialize_command(0x03, b'\x00\x64')
    result = deserialize_command(frame)
    assert result["command_id"] == 0x03
    assert result["params"] == b'\x00\x64'