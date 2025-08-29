from __future__ import annotations
from collections import namedtuple
import src.application.command.handler.impl as handler
import src.application.command.serializer.impl as codec

CommandDefinition = namedtuple("CommandDefinition", ["id", "name", "handler"])

command_definitions = {
    0x01: CommandDefinition(0x01, "REBOOT",      handler.reboot),
    0x02: CommandDefinition(0x02, "SET_MODE",    handler.set_mode),
    0x03: CommandDefinition(0x03, "TAKEOFF",     handler.takeoff),
    0x04: CommandDefinition(0x04, "LANDING",     handler.landing),
    0x05: CommandDefinition(0x05, "GIMBAL_CTRL", handler.gimbal),
    0x06: CommandDefinition(0x06, "GOTO",        handler.goto),
    0x07: CommandDefinition(0x07, "FOLLOW_ME",   handler.follow_me),
    0x09: CommandDefinition(0x09, "WAYPOINTS",   handler.waypoints),
    0x0A: CommandDefinition(0x0A, "TASK_RELAY",  handler.task_relay),
    0x0B: CommandDefinition(0x0B, "SET_SPEED", handler.set_speed),
    0x0C: CommandDefinition(0x0C, "SET_DIRECTION",   handler.set_direction),
    0x0D: CommandDefinition(0x0D, "SET_DRONE_ID",  handler.set_drone_id),
    0x0E: CommandDefinition(0x0E, "SWARM_FORMATER", handler.swarm_formater),
    0x0F: CommandDefinition(0x0F, "SWARM_LEADER",    handler.swarm_leader),
    0x10: CommandDefinition(0x10, "SWARM_MERGE", handler.swarm_merge),
    0x11: CommandDefinition(0x11, "SET_MISSION_STATUS", handler.set_mission_status),
    
    0x14: CommandDefinition(0x14, "ACK_COMMAND", handler.ack_command),
    0x15: CommandDefinition(0x15, "STREAM_VIDEO", handler.stream_video),
    0x16: CommandDefinition(0x16, "ARM_DISARM",  handler.arm_disarm),
}
