from mock_uart import MockUARTHandler
from src.tools.command_dispatcher import cmd_goto, cmd_takeoff
from src.frame_codec import parse_mesh_frame
from src.frame_router import route_frame

def handle_frames(uart, expected_count=2):
    """
    Reads and routes expected number of frames via the given UART handler.
    """
    for i in range(expected_count):
        raw_frame = uart.read()
        if not raw_frame:
            continue
        print(f"\n📥 Frame {i+1} received ({len(raw_frame)} bytes)")
        frame_dict = parse_mesh_frame(raw_frame)
        route_frame(frame_dict, uart_handler=uart)

def takeoff_test():
    uart = MockUARTHandler()
    uart.start()

    # Generate TAKEOFF frame and inject into UART
    frame = cmd_takeoff(
        takeoff_alt=50.0,
        dst=2,
        src=1,
        return_only=True  # Only return frame instead of sending
    )
    uart.inject_frame(frame)

    handle_frames(uart, expected_count=2)
    uart.stop()

def goto_test():
    uart = MockUARTHandler()
    uart.start()

    # Generate GOTO frame and inject into UART
    frame = cmd_goto(
        target_lat=41.5438,
        target_lon=31.5565,
        target_alt=80.0,
        dst=1,
        src=1,
        return_only=True
    )
    uart.inject_frame(frame)

    handle_frames(uart, expected_count=2)
    uart.stop()

def main():
    goto_test()
    # takeoff_test()  # Uncomment to run takeoff test

if __name__ == "__main__":
    main()
