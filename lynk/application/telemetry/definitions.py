from __future__ import annotations
from collections import namedtuple
import lynk.application.telemetry.handler.impl as handler


TelemetryDefinition = namedtuple("TelemetryDefinition", ["id", "name", "handler", "serialize", "deserialize"])

# Helper to lazy load definitions
class TelemetryDefinitionsDict(dict):
    def __init__(self):
         self._loaded = False
    
    def _load(self):
        if self._loaded:
            return
        
        from lynk.application.telemetry.serializer.dispatcher import _get_tlm_fields, serialize_telemetry, deserialize_telemetry
        import lynk.application.telemetry.handler.impl as handler
        
        tlm_fields = _get_tlm_fields()
        
        for name, (field_name, _, tlm_id) in tlm_fields.items():
            handler_func = getattr(handler, field_name, None)
            if handler_func is None:
                handler_func = handler.default_handler
            
            # Create a bound serializer for this specific telemetry type
            # We use a default argument to capture the loop variable 'name'
            def create_serializer(n=name):
                return lambda *args: serialize_telemetry(n, *args)
            
            # Deserializer is generic in dispatcher, returning dict with fields
            self[tlm_id] = TelemetryDefinition(
                tlm_id, 
                name, 
                handler_func, 
                create_serializer(), 
                deserialize_telemetry
            )
            
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

telemetry_definitions = TelemetryDefinitionsDict()
