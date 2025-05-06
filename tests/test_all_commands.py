from src.core.frame_codec import parse_mesh_frame
from src.core.frame_router import route_frame
from src.tools.comm.interface_factory import create_interface
from src.tools.command.command_builder import (
    build_cmd_reboot,
    build_cmd_set_mode,
    build_cmd_takeoff,
    build_cmd_landing,
    build_cmd_gimbal,
    build_cmd_goto,
    build_cmd_simple_follow_me,
    build_cmd_waypoints
)

def handle_frames(interface, expected_count=1):
    """
    Interface (UART/UDP) üzerinden gelen frame'leri işler.
    """
    for i in range(expected_count):
        raw = interface.read()
        if not raw:
            continue
        print(f"\n📥 Frame {i+1} received ({len(raw)} bytes)")
        frame_dict = parse_mesh_frame(raw)
        route_frame(frame_dict, uart_handler=interface)

def test_all_commands():
    interface = create_interface() 

    print("\n[TEST] REBOOT")
    frame = build_cmd_reboot(dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] SET_MODE")
    frame = build_cmd_set_mode(mode=3, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] TAKEOFF (simple)")
    frame = build_cmd_takeoff(takeoff_alt=40, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] TAKEOFF (with coords)")
    frame = build_cmd_takeoff(takeoff_alt=40, target_lat=37.0, target_lon=32.0, target_alt=100.0, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] LAND (simple)")
    frame = build_cmd_landing(dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] LAND (with coords)")
    frame = build_cmd_landing(target_lat=37.1, target_lon=32.1, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] GIMBAL CONTROL")
    frame = build_cmd_gimbal(yaw=10.0, pitch=20.0, roll=5.0, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] GOTO")
    frame = build_cmd_goto(target_lat=41.0, target_lon=29.0, target_alt=150.0, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] FOLLOW_ME")
    frame = build_cmd_simple_follow_me(target_id=42, altitude=75.0, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    print("\n[TEST] WAYPOINTS")
    waypoints = [(37.0, 32.0, 100.0), (37.1, 32.1, 110.0), (37.2, 32.2, 120.0)]
    frame = build_cmd_waypoints(waypoints, dst=1, src=1)
    interface.send(frame)
    handle_frames(interface)

    # interface.uart.stop() çağrısı istersen sona eklenebilir (UART/UDP ortak stop yöntemi için)

if __name__ == "__main__":
    test_all_commands()
