def test_swarm_commander_import():
    from src.swarm.swarm_commander import send_goto
    assert callable(send_goto)