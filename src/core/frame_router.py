# src/frame_router.py

from src.handlers.command.command_handler import handle_command
from src.handlers.telemetry.telemetry_handler import handle_telemetry
from src.handlers.swarm.swarm_handler import handle_swarm
from src.handlers.ack.ack_handler import handle_ack

from src.core.frame_codec import load_device_id
from src.tools.comm.interfaces import UARTInterface  # ✅ interface soyutlamasını getir
from src.tools.log.logger import logger

# Frame Type → Handler Mapping
dispatch_table = {
    'C': handle_command,
    'T': handle_telemetry,
    'S': handle_swarm,
    'A': handle_ack
}

def route_frame(frame_dict: dict, uart_handler=None):
    """
    Routes a decoded mesh frame to the appropriate handler.
    """

    try:
        frame_type = frame_dict.get("frame_type")
        dst_id = frame_dict.get("dst_id")
        payload = frame_dict.get("payload")

        # Convert frame_type to character if it's an integer
        if isinstance(frame_type, int):
            frame_type = chr(frame_type)

        local_id = load_device_id()

        if dst_id != 0xFF and dst_id != local_id:
            logger.debug(f"[ROUTER] IGNORED | Frame not addressed to this node (dst_id={dst_id}, local_id={local_id})")
            return

        handler = dispatch_table.get(frame_type)

        if handler:
            logger.info(f"[ROUTER] RECEIVED | FRAME_TYPE='{frame_type}' | SRC: {frame_dict['src_id']} -> DST: {frame_dict['dst_id']}")
            logger.info(f"[ROUTER] DISPATCHED | FRAME_TYPE='{frame_type}' | HANDLER: {handler.__name__}")

            # ✅ interface üretimi
            interface = UARTInterface(uart_handler)

            # ✅ handler çağrısına interface gönder
            handler(payload, frame_dict, interface)
        else:
            logger.warning(f"[ROUTER] UNKNOWN FRAME_TYPE | '{frame_type}' from SRC: {frame_dict['src_id']}")

    except Exception as e:
        logger.error(f"[ROUTER] ERROR | Exception while routing frame: {e}")
