from __future__ import annotations
from collections import namedtuple
import lynk.application.event.handler.impl as handler
from lynk.shared.log.logger import logger

EventDefinition = namedtuple("EventDefinition", ["id", "name", "handler"])

class EventDefinitionsDict(dict):
    def __init__(self):
        self._loaded = False
    
    def _load(self):
        if self._loaded:
            return
        
        from lynk.application.event.serializer.dispatcher import get_event_payload_schema
        event_map = get_event_payload_schema()
        
        for event_id, (field_name, _) in event_map.items():
            handler_func = getattr(handler, field_name, None)
            
            if not handler_func:
                handler_func = handler.default_handler
                logger.debug(f"[EVENT] Using default_handler for event '{field_name}' (ID: {event_id})")
            
            name = field_name.upper()
            self[event_id] = EventDefinition(event_id, name, handler_func)
        
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

event_definitions = EventDefinitionsDict()
