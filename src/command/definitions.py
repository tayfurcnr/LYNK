from collections import namedtuple
import src.command.handler.impl as handler
import src.command.serializer.impl as codec

CommandDefinition = namedtuple("CommandDefinition", ["id", "name", "handler"])

command_definitions = {
    0x01: CommandDefinition(0x01, "REBOOT",      handler.reboot),
    0x02: CommandDefinition(0x02, "SET_MODE",    handler.set_mode),
    0x03: CommandDefinition(0x03, "TAKEOFF",     handler.takeoff),
    0x04: CommandDefinition(0x04, "LANDING",     handler.landing),
    0x05: CommandDefinition(0x05, "GIMBAL_CTRL", handler.gimbal),
    0x06: CommandDefinition(0x06, "GOTO",        handler.goto),
    0x07: CommandDefinition(0x07, "FOLLOW_ME",   handler.follow_me),
    0x09: CommandDefinition(0x08, "WAYPOINTS",   handler.waypoints),
}
