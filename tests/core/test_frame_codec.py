def test_frame_build_and_parse():
    from src.core.frame_codec import build_mesh_frame, parse_mesh_frame
    frame = build_mesh_frame('T', src_id=1, dst_id=2, payload=b'ABC')
    parsed = parse_mesh_frame(frame)
    assert chr(parsed['frame_type']) == 'T'
    assert parsed['src_id'] == 1
    assert parsed['dst_id'] == 2
    assert parsed['payload'] == b'ABC'