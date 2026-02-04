# Automation of Protocol Mapping

## Goal
Eliminate manual updates to `definitions.py` and `dispatcher.py` when adding new Commands or Telemetry. The system will automatically discover mappings and handlers using Protobuf introspection and Python conventions.

## User Review Required
> [!WARNING]
> This change modifies the wire format by reassigning field tags in `CommandEnvelope` and `TelemetryEnvelope`. This breaks compatibility with existing `lynk-v2` binaries appearing in previous builds. The `cmd_id` and `tlm_id` fields are moved to tag 255.

## Proposed Changes

### Shared
#### [MODIFY] [Command Dispatcher](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/application/command/serializer/dispatcher.py)
- Remove hardcoded `_CMD_MAP`.
- Implement `_build_cmd_map()` that iterates `CommandEnvelope.DESCRIPTOR.oneofs_by_name['payload'].fields`.
- Map `field.number` -> ID.
- Map `field.name` -> Name.
- Extract inner message fields dynamically.

#### [MODIFY] [Telemetry Dispatcher](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/application/telemetry/serializer/dispatcher.py)
- Remove hardcoded `_TLM_FIELDS`.
- Implement dynamic mapping similar to Command Dispatcher.

#### [MODIFY] [Command Definitions](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/application/command/definitions.py)
- Use `importlib` and `pkgutil` or simple `getattr` from `handler.impl` to find handlers matching the command name.
- Dynamically build `command_definitions`.

#### [MODIFY] [Telemetry Definitions](file:///home/tayfurcnr/Desktop/HiroMarker/LYNK/src/application/telemetry/definitions.py)
- Similar dynamic discovery for telemetry handlers.

## Verification Plan

### Automated Tests
- Run existing tests `pytest tests/test_platform.py` to ensure existing commands still work.
- Create a temporary new proto file (e.g., `msg/command/test_auto.proto`), regenerate, and verify `dispatcher` picks it up without code changes.

### Manual Verification
- Check `main.py` execution to ensure system boots without `KeyError` or `ImportError`.
