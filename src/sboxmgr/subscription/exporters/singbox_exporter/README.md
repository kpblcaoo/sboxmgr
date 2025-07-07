# Sing-box Exporter Module

This module provides modular sing-box configuration export functionality, refactored from the original monolithic `singbox_exporter.py` file.

## Module Structure

```
singbox_exporter/
├── __init__.py              # Main exports and package interface
├── constants.py             # Constants and configuration values
├── core.py                  # Core export functions
├── config_processors.py     # Configuration processing utilities
├── protocol_handlers.py     # Special protocol handlers
├── inbound_generator.py     # Inbound configuration generation
├── legacy.py               # Legacy/deprecated functions
└── README.md               # This documentation
```

## Architecture

The module follows the Single Responsibility Principle (SRP) by separating concerns into specialized modules:

### Core Components

1. **constants.py** - All constants and configuration values
2. **core.py** - Main export functions (`singbox_export`, `singbox_export_with_middleware`)
3. **config_processors.py** - Configuration processing and validation
4. **protocol_handlers.py** - Special protocol handlers (WireGuard, Hysteria2, etc.)
5. **inbound_generator.py** - Inbound configuration generation
6. **legacy.py** - Deprecated functions for backward compatibility

### Key Features

- **Modular Design**: Each component has a single responsibility
- **Type Safety**: Full type hints throughout
- **Protocol Support**: Handles all major proxy protocols
- **Modern Approach**: Uses sing-box 1.11.0+ rule actions instead of legacy special outbounds
- **Backward Compatibility**: Legacy functions available for older code

## Usage

### Basic Export

```python
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export

# Export servers to sing-box configuration
config = singbox_export(servers, routes=None, client_profile=None)
```

### With Middleware

```python
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export_with_middleware

# Export with middleware support
config = singbox_export_with_middleware(
    servers=servers,
    routes=routes,
    client_profile=client_profile,
    context=pipeline_context
)
```

### Protocol Handlers

```python
from sboxmgr.subscription.exporters.singbox_exporter import (
    export_wireguard,
    export_hysteria2,
    get_protocol_dispatcher
)

# Use specific protocol handler
wireguard_config = export_wireguard(server)

# Get all protocol handlers
dispatcher = get_protocol_dispatcher()
```

## Benefits

1. **Maintainability**: Easier to modify and extend individual components
2. **Testability**: Each module can be tested independently
3. **Readability**: Clear separation of concerns
4. **Reusability**: Components can be used independently
5. **Performance**: Only import what you need

## Migration

The original `singbox_exporter.py` file has been preserved as a compatibility layer. All existing code will continue to work without changes.

To use the new modular version:

```python
# Old way (still works)
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export

# New way (recommended)
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export
```

## Refactoring Statistics

- **Before**: 1 file, 1010 lines
- **After**: 7 files, ~800 lines (excluding legacy.py)
- **Improvement**: Better organization, maintainability, and testability

## Protocol Support

Supported protocols:
- VLESS, VMess, Trojan
- Shadowsocks
- WireGuard
- Hysteria2
- TUIC
- ShadowTLS
- AnyTLS
- Tor
- SSH

## Configuration Processing

The module handles:
- Transport configuration (WebSocket, gRPC, TCP, UDP)
- TLS configuration (including Reality)
- Authentication and flow control
- Tag management
- Additional parameters validation
