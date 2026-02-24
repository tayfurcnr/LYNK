from __future__ import annotations
from collections import namedtuple
import lynk.application.command.handler.impl as handler
from lynk.shared.log.logger import logger

CommandDefinition = namedtuple("CommandDefinition", ["id", "name", "handler"])

# Helper to lazy load definitions
class CommandDefinitionsDict(dict):
    def __init__(self):
         self._loaded = False
    
    def _load(self):
        if self._loaded:
            return
        
        from lynk.application.command.serializer.dispatcher import _get_cmd_map
        cmd_map = _get_cmd_map()
        
        for cmd_id, (field_name, _) in cmd_map.items():
            # Convention: field_name 'system_reboot' -> handler 'system_reboot'
            handler_func = getattr(handler, field_name, None)
            name = field_name.upper()
            
            # If no specific handler is found, use the default bridge handler
            if not handler_func:
                 handler_func = (
                     lambda cid, params, src_id, interface, _name=name:
                     handler.default_handler(cid, params, src_id, interface, cmd_name=_name)
                 )
                 logger.debug(f"[COMMAND] Using default_handler for command '{field_name}' (ID: {cmd_id})")
            
            self[cmd_id] = CommandDefinition(cmd_id, name, handler_func)
        
        self._loaded = True

    def __getitem__(self, key):
        self._load()
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._load()
        return super().get(key, default)
    
    def items(self):
        self._load()
        return super().items()
    
    def values(self):
        self._load()
        return super().values()

command_definitions = CommandDefinitionsDict()
