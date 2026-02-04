# Protocol Automation Walkthrough

I have successfully automated the protocol mapping process for both Commands and Telemetry. The system now dynamically discovers message structures and handlers using Protobuf introspection, eliminating the need for manual updates to definition files.

## Changes

### Dynamic Dispatchers
Refactored `src/application/command/serializer/dispatcher.py` and `src/application/telemetry/serializer/dispatcher.py` to:
- **Introspect Protobuf Envelopes**: Instead of hardcoded maps, the system now inspects `CommandEnvelope.payload` and `TelemetryEnvelope.payload` oneofs at runtime.
- **Auto-Discovery**: It automatically maps the Field ID (tag) to the Field Name, and extracts parameter names from the inner message definitions.

### Auto-Discovery Definitions
Refactored `src/application/command/definitions.py` and `src/application/telemetry/definitions.py` to:
- **Lazy Loading**: Definitions are built on first access to ensure all Protobuf modules are loaded.
- **Dynamic Binding**: Handlers are looked up by name (matching the Protobuf field name) in `src/application/*/handler/impl.py`.
- **Automatic Serialization**: Telemetry serializers are automatically generated as partial functions wrapping the generic `serialize_telemetry`.

## Verification Results

### Serialization Tests
I ran unit tests to verify that the new dynamic system correctly serializes and deserializes messages.

#### Command Serialization
`tests/command/test_command_serialization.py`: **PASSED**
- Verified that `serialize_command(ID, params)` correctly creates a Protobuf payload.
- Verified that `deserialize_command(payload)` correctly retrieves the ID and parameters.

#### Telemetry Serialization
`tests/telemetry/test_telemetry_serialization.py`: **PASSED**
- Verified `GPS` telemetry serialization using the new dynamic lookup.
- Verified that `telemetry_definitions` correctly binds the dynamic serializer and deserializer.

## Bug Fixes

### Relay Sequence Number Bug
- **Issue**: Relayed frames were being assigned new sequence numbers, determining them as "fresh" packets by receivers, causing duplicate command execution.
- **Fix**: Updated `frame_codec.py` to allow manual sequence number injection and `frame_router.py` to preserve the original sequence number during relay.
- **Verification**: Verified that receivers correctly identify relayed packets as "Replay detected" and reject them, ensuring commands execute only once.
- **Note**: "Replay detected" warnings in the log are expected behavior and indicate the security system is successfully blocking duplicate or relayed frames. You may also see `LAST: X` in the warning, which refers to the sequence number of the most recent frame (Command or Telemetry) accepted from that source.

## Usage
No changes are required for existing usage. Adding a new command now only requires:
1. Defining the message in `.proto`.
2. Adding it to the `Envelope`.
3. Adding a handler function in `impl.py` with the same name.
The system will handle the rest automatically.
