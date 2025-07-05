# Agent Bridge Usage Guide

## Overview

The Agent Bridge provides a standardized interface for communicating with external `sboxagent` processes. This allows sboxmgr to delegate validation, installation, and client management tasks to a separate agent process.

## Architecture

```
┌─────────────┐    JSON API    ┌─────────────┐
│   sboxmgr   │ ──────────────► │  sboxagent  │
│   (Python)  │ ◄────────────── │ (Go/Ruby/?) │
└─────────────┘                └─────────────┘
```

## CLI Usage

### Basic Usage

```bash
# Use internal validation (default)
sboxmgr run -u "subscription_url"

# Use external agent validation
sboxmgr run -u "subscription_url" --with-agent-check
```

### Agent Check Output

When `--with-agent-check` is used:

```bash
✅ External validation passed
   Detected client: sing-box
   Client version: 1.8.0
📦 Available clients: sing-box, xray
```

If agent is not available:
```bash
ℹ️  sboxagent not available - skipping external validation
```

## Python API Usage

### Basic Agent Operations

```python
from sboxmgr.agent import AgentBridge, ClientType
from pathlib import Path

# Initialize bridge
bridge = AgentBridge()

# Check if agent is available
if bridge.is_available():
    # Validate configuration
    response = bridge.validate(
        config_path=Path("/path/to/config.json"),
        client_type=ClientType.SING_BOX
    )
    
    if response.success:
        print("Validation passed!")
    else:
        print(f"Validation failed: {response.errors}")
    
    # Check available clients
    check_response = bridge.check()
    print(f"Available clients: {check_response.clients}")
    
    # Install a client
    install_response = bridge.install(
        client_type=ClientType.SING_BOX,
        version="1.8.0"
    )
```

### Error Handling

```python
from sboxmgr.agent import AgentBridge, AgentNotAvailableError, AgentError

try:
    bridge = AgentBridge()
    response = bridge.validate(Path("/config.json"))
except AgentNotAvailableError:
    print("Agent not available, using internal validation")
    # Fallback to internal validation
except AgentError as e:
    print(f"Agent operation failed: {e}")
```

## JSON API Protocol

### Request Format

All requests follow this structure:

```json
{
    "command": "validate|install|check|version",
    "version": "1.0",
    "trace_id": "optional-trace-id",
    // Command-specific fields...
}
```

### Validation Request

```json
{
    "command": "validate",
    "version": "1.0",
    "config_path": "/path/to/config.json",
    "client_type": "sing-box",
    "strict": true,
    "trace_id": "req-123"
}
```

### Validation Response

```json
{
    "success": true,
    "message": "Validation passed",
    "trace_id": "req-123",
    "errors": [],
    "client_detected": "sing-box",
    "client_version": "1.8.0"
}
```

### Installation Request

```json
{
    "command": "install",
    "version": "1.0",
    "client_type": "sing-box",
    "version": "1.8.0",
    "force": false
}
```

### Check Request

```json
{
    "command": "check",
    "version": "1.0",
    "client_type": null
}
```

### Check Response

```json
{
    "success": true,
    "message": "Check completed",
    "clients": {
        "sing-box": {
            "available": true,
            "version": "1.8.0",
            "path": "/usr/bin/sing-box"
        },
        "xray": {
            "available": false,
            "error": "Not found in PATH"
        }
    }
}
```

## Agent Implementation Contract

### Command Line Interface

The agent must support:

```bash
# JSON mode (required)
sbox-agent --json < request.json

# Individual commands (optional)
sbox-agent validate --input config.json
sbox-agent install --client sing-box --version 1.8.0
sbox-agent check
```

### Communication Protocol

1. **Input**: JSON request via stdin when using `--json`
2. **Output**: JSON response via stdout
3. **Logging**: Technical logs via stderr
4. **Exit Codes**: 0 for success, non-zero for failure

### Error Handling

- **Success**: `{"success": true, "message": "..."}`
- **Failure**: `{"success": false, "message": "...", "error_code": "..."}`
- **Technical logs**: Always to stderr, never to stdout

## Future Enhancements

### Service Mode Integration

```python
# Future: systemd service communication
bridge = AgentBridge(
    mode="service",
    socket_path="/run/sboxagent.sock"
)

# Event-driven updates
bridge.subscribe_to_events(["config_updated", "client_installed"])
```

### Agent Discovery

```python
# Future: Multiple agent support
bridge = AgentBridge()
agents = bridge.discover_agents()  # Find all available agents
bridge.select_agent("sboxagent-go")  # Choose specific implementation
```

## Supported Client Types

- `sing-box`: SingBox VPN client
- `xray`: Xray-core
- `clash`: Clash/ClashMeta
- `hysteria`: Hysteria protocol
- `mihomo`: Mihomo (Clash Meta fork)

## Configuration

### Environment Variables

```bash
# Agent path override
export SBOXAGENT_PATH="/usr/local/bin/sbox-agent"

# Agent timeout (seconds)
export SBOXAGENT_TIMEOUT=60

# Enable agent debug logging
export SBOXAGENT_DEBUG=1
```

### Agent Auto-Discovery

The bridge automatically searches for agents in this order:

1. `sbox-agent` in PATH
2. `sboxagent` in PATH
3. Environment variable `SBOXAGENT_PATH`

## Benefits

### For sboxmgr
- **Decoupled validation**: No hard dependency on sing-box binary
- **Enhanced error reporting**: Structured validation messages
- **Multi-client support**: Validate configs for different VPN clients
- **Installation automation**: Automated client installation

### For sboxagent
- **Language flexibility**: Can be implemented in Go, Rust, C++, etc.
- **Performance**: Native binary performance for validation
- **System integration**: Direct OS integration for installation
- **Service mode**: Can run as system daemon

## Migration Path

1. **Phase 1** ✅: Internal validation (current)
2. **Phase 2** ✅: Agent bridge infrastructure
3. **Phase 3**: sboxagent implementation
4. **Phase 4**: Service mode integration
5. **Phase 5**: Event-driven architecture 