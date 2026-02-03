from __future__ import annotations
from collections import namedtuple
import src.application.command.handler.impl as handler
import src.application.command.serializer.impl as codec

CommandDefinition = namedtuple("CommandDefinition", ["id", "name", "handler"])

command_definitions = {
    0x01: CommandDefinition(0x01, "SYSTEM_REBOOT",      handler.system_reboot),
    0x02: CommandDefinition(0x02, "SYSTEM_SET_VEHICLE_ID", handler.system_set_vehicle_id),
    0x03: CommandDefinition(0x03, "SYSTEM_SET_TEAM_ID",    handler.system_set_team_id),

    0x15: CommandDefinition(0x15, "FLIGHT_SET_MODE", handler.flight_set_mode),
    0x16: CommandDefinition(0x16, "FLIGHT_ARMING",  handler.flight_arming),
    0x17: CommandDefinition(0x17, "FLIGHT_TAKEOFF", handler.flight_takeoff),
    0x18: CommandDefinition(0x18, "FLIGHT_GOTO",    handler.flight_goto),
    0x19: CommandDefinition(0x19, "FLIGHT_SET_SPEED", handler.flight_set_speed),
    0x1A: CommandDefinition(0x1A, "FLIGHT_SET_ALTITUDE", handler.flight_set_altitude),
    0x1B: CommandDefinition(0x1B, "FLIGHT_SET_HEADING", handler.flight_set_heading),
    0x1C: CommandDefinition(0x1C, "FLIGHT_SET_HOME", handler.flight_set_home),
    0x1D: CommandDefinition(0x1D, "FLIGHT_SET_ROI", handler.flight_set_roi),
    0x1E: CommandDefinition(0x1E, "FLIGHT_LAND", handler.flight_land),

    # Görev Komutları
    0x29: CommandDefinition(0x29, "MISSION_UPLOAD", handler.mission_upload),
    0x2A: CommandDefinition(0x2A, "MISSION_CONTROL", handler.mission_control),

    # Swarm Komutları
    0x3D: CommandDefinition(0x3D, "SWARM_FORMATION_EXECUTE", handler.swarm_formation_execute),
    0x3E: CommandDefinition(0x3E, "SWARM_SET_LEADER", handler.swarm_set_leader),
    0x3F: CommandDefinition(0x3F, "SWARM_SET_FORMATION_TYPE", handler.swarm_set_formation_type),
    0x40: CommandDefinition(0x40, "SWARM_SET_SPACING", handler.swarm_set_spacing),
    0x41: CommandDefinition(0x41, "SWARM_SET_ALTITUDE_OFFSET", handler.swarm_set_altitude_offset),
    0x42: CommandDefinition(0x42, "SWARM_SET_STATUS", handler.swarm_set_status),
}
