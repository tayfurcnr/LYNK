from __future__ import annotations

from lynk.application.command.definitions import command_definitions


def test_trajectory_commands_are_bound():
    set_alg = command_definitions.get(99)
    exec_traj = command_definitions.get(101)

    assert set_alg is not None
    assert exec_traj is not None
    assert set_alg.name == "SET_TRAJECTORY_ALGORITHM"
    assert exec_traj.name == "TRAJECTORY_EXECUTE"
    assert getattr(set_alg.handler, "__name__", "") == "set_trajectory_algorithm"
    assert getattr(exec_traj.handler, "__name__", "") == "trajectory_execute"


def test_trajectory_handlers_accept_valid_payloads():
    set_alg = command_definitions.get(99)
    exec_traj = command_definitions.get(101)

    set_alg.handler(99, {"algorithm_type": 1, "param1": 0.5}, src_id=1, interface=None)
    exec_traj.handler(101, {"enable": True}, src_id=1, interface=None)
