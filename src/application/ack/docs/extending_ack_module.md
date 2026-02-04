# 🛡️ ACK Module: Developer Guide

Handles Acknowledgement (onay) mechanisms.

## 📁 Structure
- `definitions.py`: Registry for ACK IDs and handlers.
- `handler/impl.py`: Logic executed when an ACK arrives.
- `serializer/dispatcher.py`: Protobuf-based serialization logic.
- `tools/dispatcher.py`: High-level functions to send standard ACKs.

## 🛠 Adding an ACK Type
The ACK module uses **Protobuf Envelopes**. To add a custom status:

### 1. Define Schema
Add a new `.proto` file in `msg/ack/` or update an existing one.

### 2. Register Envelope
Update `msg/ack/ack_envelope.proto`:
```protobuf
message AckEnvelope {
  uint32 ack_id = 1;
  oneof payload {
    // ...
    ExecutionDenied execution_denied = 7;
  }
}
```

### 3. Registry & Logic
1. Run `python3 setup.py protos`.
2. Update `definitions.py` to map the new ID to a handler.
3. Implement the handler in `handler/impl.py`.

## 🚀 Dispatching ACKs
Use the dispatcher for consistent reporting. It handles the dynamic Protobuf wrapping for you:
```python
from src.application.ack.tools.dispatcher import send_ack_ok
send_ack_ok(interface, cmd_id=1, dst=10)
```