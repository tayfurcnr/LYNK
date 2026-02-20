import os
import sys

# Automatically add the internal protobuf directory to sys.path
# This allows generated protobuf files to perform their internal imports 
# (e.g. 'from msg.command import ...') without extra hacks in user scripts.
_proto_dir = os.path.join(os.path.dirname(__file__), "shared", "proto")
if _proto_dir not in sys.path:
    sys.path.insert(0, _proto_dir)

# --- PUBLIC API FACADE ---
# These imports make 'import lynk' powerful and easy to use.

# 1. Configuration Management
from lynk.shared.config import manager as config

# 2. Communication Setup
from lynk.shared.comm.interface_factory import create_interface

# 3. Application Layers (Dispatchers & Caches)
from lynk.application.telemetry.tools import dispatcher as telemetry
from lynk.application.telemetry.tools import builder as telemetry_builder
from lynk.application.telemetry.tools import cache as tlm_cache
from lynk.application.telemetry.handler.dispatcher import handle_telemetry
from lynk.application.command.tools import dispatcher as command
from lynk.application.command.tools import cache as cmd_cache
from lynk.application.command.definitions import command_definitions
from lynk.application.ack.definitions import ack_definitions
from lynk.application.ack.serializer.dispatcher import deserialize_ack
from lynk.application.result.serializer.dispatcher import deserialize_result
from lynk.application.event.tools import dispatcher as event
from lynk.application.event.definitions import event_definitions
from lynk.application.event.serializer.dispatcher import deserialize_event
from lynk.application.event.serializer.dispatcher import get_event_payload_schema
from lynk.application.mavlink.tools import dispatcher as mavlink
from lynk.application.mavlink.serializer.dispatcher import deserialize_mavlink
from lynk.application.mavlink.serializer.dispatcher import serialize_mavlink

# 3a. MAVLink ROS Integration (optional, requires ROS)
try:
    from lynk.application.mavlink.ros import converter as ros
except ImportError:
    ros = None  # ROS not available

# 4. Core Components (for advanced users)
from lynk.core import frame_codec as codec
from lynk.core import frame_router as router
from lynk.core.sequence_manager import get_sequence_manager

def process(raw_data: bytes, interface) -> bool:
    """Convenience alias for router.process"""
    return router.process(raw_data, interface)

__version__ = "1.1.0"

# Metadata for easy discovery
__all__ = [
    "config",
    "create_interface",
    "telemetry",
    "telemetry_builder",
    "tlm_cache",
    "command",
    "cmd_cache",
    "command_definitions",
    "ack_definitions",
    "deserialize_ack",
    "deserialize_result",
    "event",
    "event_definitions",
    "deserialize_event",
    "get_event_payload_schema",
    "mavlink",
    "deserialize_mavlink",
    "serialize_mavlink",
    "ros",
    "codec",
    "router",
    "get_sequence_manager",
    "process",
    "handle_telemetry"
]


def __getattr__(name):
    """Compatibility aliases for older/newer integration points."""
    if name == "telemetry_builder":
        from lynk.application.telemetry.tools import builder as _builder

        return _builder
    raise AttributeError(f"module 'lynk' has no attribute '{name}'")
