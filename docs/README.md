# LYNK Toolkit Documentation

## Project Overview
LYNK is a mesh networking toolkit for UAV communication with advanced features including:
- Dynamic protocol mapping using Protobuf
- Encrypted communication (AES-GCM)
- Anti-replay protection
- Multi-hop relay support
- Automatic command and telemetry discovery

## Documentation Structure

### Core Documentation
- [`implementation_plan.md`](implementation_plan.md) - Protocol automation implementation plan
- [`walkthrough.md`](walkthrough.md) - Summary of completed work and verification

### Guides
- [`guides/command_guide.md`](guides/command_guide.md) - How to add new commands
- [`guides/telemetry_guide.md`](guides/telemetry_guide.md) - How to add new telemetry types
- [`guides/compass_example.md`](guides/compass_example.md) - Practical example of adding COMPASS telemetry

## Installation
 
### For Users (Production/Runtime)
To install only the essential libraries needed to run the toolkit:
```bash
pip install -r requirements.txt
```

### For Developers (Testing & UI)
To install everything, including `pytest` and the **Web Dashboard**:
```bash
pip install -r requirements-dev.txt
```

## Quick Start

### Adding a New Command
1. Define message in `msg/command/your_command.proto`
2. Add to `msg/command/command_envelope.proto`
3. Run `python3 setup.py protos`
4. Add handler in `lynk/application/command/handler/impl.py`

### Adding a New Telemetry
1. Define message in `msg/telemetry/your_telemetry.proto`
2. Add to `msg/telemetry/telemetry_envelope.proto`
3. Run `python3 setup.py protos`
4. Use `send_telemetry(interface, "YOUR_TELEMETRY", param1=value1, ...)`

### Running the Test Lab
1. Run `python3 test_lab.py`
2. Access at `http://localhost:8000`

## Key Features

### Automatic Protocol Mapping
- Protobuf introspection for dynamic discovery
- No hardcoded mappings
- Type-safe serialization/deserialization

### Security
- AES-256-GCM encryption
- Sequence number-based replay protection
- Team-based filtering

### Mesh Networking
- Multi-hop relay with TTL
- Duplicate detection
- Broadcast and unicast support

## Configuration

See `configs/node_X/config.yaml` for node-specific settings:
- Vehicle ID and Team ID
- Security keys
- Relay settings
- Interface configuration (UDP/UART)
