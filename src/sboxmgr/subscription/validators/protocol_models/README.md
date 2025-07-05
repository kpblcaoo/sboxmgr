# Protocol Models Module

This module provides comprehensive Pydantic models for validating VPN protocol configurations. It implements **ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation**.

## Architecture

The module is organized into specialized submodules for better maintainability:

### 📁 Module Structure

```
protocol_models/
├── __init__.py          # Package exports and public API
├── enums.py             # Common enumeration types
├── transport.py         # Transport layer configurations
├── common.py            # Shared models across protocols
├── protocol_configs.py  # Protocol-specific configurations
├── outbound_models.py   # Outbound configurations for sing-box
├── validators.py        # Validation utilities and functions
└── README.md           # This documentation
```

### 📋 Module Responsibilities

| Module | Responsibility | Key Components |
|--------|----------------|----------------|
| `enums.py` | Common enumeration types | `LogLevel`, `DomainStrategy`, `Network` |
| `transport.py` | Transport layer configurations | `WsConfig`, `HttpConfig`, `GrpcConfig`, `QuicConfig` |
| `common.py` | Shared models across protocols | `TlsConfig`, `StreamSettings`, `MultiplexConfig` |
| `protocol_configs.py` | Protocol-specific configurations | `ShadowsocksConfig`, `VmessConfig`, `VlessConfig`, `TrojanConfig`, `WireGuardConfig` |
| `outbound_models.py` | Outbound configurations for sing-box | `OutboundBase`, `*Outbound` classes |
| `validators.py` | Validation utilities and functions | `validate_protocol_config`, `generate_protocol_schema` |

## Supported Protocols

- **Shadowsocks**: SOCKS5 proxy with various encryption methods
- **VMess**: V2Ray protocol with transport layer options
- **VLESS**: Xray protocol with XTLS support
- **Trojan**: TLS-based proxy protocol
- **WireGuard**: Modern VPN protocol

## Usage Examples

### Basic Validation

```python
from sboxmgr.subscription.validators.protocol_models import validate_protocol_config

# Validate Shadowsocks configuration
config_dict = {
    "server": "example.com",
    "server_port": 8388,
    "password": "my_password",
    "method": "aes-256-gcm"
}

shadowsocks_config = validate_protocol_config(config_dict, "shadowsocks")
```

### Schema Generation

```python
from sboxmgr.subscription.validators.protocol_models import generate_protocol_schema

# Generate JSON schema for VMess protocol
vmess_schema = generate_protocol_schema("vmess")
```

### Outbound Configuration

```python
from sboxmgr.subscription.validators.protocol_models import (
    validate_outbound_config,
    convert_protocol_to_outbound
)

# Create outbound configuration for sing-box
outbound_config = {
    "type": "shadowsocks",
    "tag": "proxy",
    "server": "example.com",
    "server_port": 8388,
    "method": "aes-256-gcm",
    "password": "my_password"
}

outbound = validate_outbound_config(outbound_config)
```

## Key Features

### 🔧 Comprehensive Validation
- **Type Safety**: Full Pydantic typing with validation
- **Field Validation**: Custom validators for protocol-specific fields
- **Error Messages**: Detailed error messages for invalid configurations

### 🏗️ Modular Design
- **Single Responsibility**: Each module has a clear, focused purpose
- **Reusability**: Components can be used independently
- **Maintainability**: Easy to modify and extend individual protocols

### 📊 Schema Generation
- **JSON Schema**: Automatic generation from Pydantic models
- **Documentation**: Self-documenting models with descriptions
- **Validation**: Consistent validation across all protocols

### 🔄 Format Conversion
- **Protocol to Outbound**: Convert internal configs to sing-box format
- **Dictionary Support**: Create configurations from dictionaries
- **Flexible Input**: Support for multiple input formats

## Transport Layer Support

### Supported Transports
- **TCP**: Direct TCP connections
- **WebSocket**: WebSocket transport with headers
- **HTTP/2**: HTTP/2 transport with host configuration
- **gRPC**: gRPC transport with service configuration
- **QUIC**: QUIC transport with TLS support

### TLS Configuration
- **Standard TLS**: Basic TLS with certificate validation
- **Reality**: SNI protection with Reality protocol
- **uTLS**: Browser fingerprint emulation
- **XTLS**: Enhanced TLS for better performance

## Error Handling

The module provides comprehensive error handling:

```python
try:
    config = validate_protocol_config(invalid_config, "shadowsocks")
except ValueError as e:
    print(f"Validation error: {e}")
```

## Dependencies

- `pydantic`: Core validation framework
- `typing`: Type hints and unions
- `enum`: Enumeration types

## Migration from Original File

This module replaces the original `protocol_models.py` file (661 lines) with a modular architecture:

- **Before**: Single 661-line file with all protocol models
- **After**: 6 specialized modules with clear responsibilities
- **Benefits**: Better maintainability, easier testing, improved organization

## Performance Considerations

- **Lazy Loading**: Modules are loaded only when needed
- **Efficient Validation**: Pydantic's optimized validation
- **Memory Usage**: Reduced memory footprint through modular design

## Testing

Each module can be tested independently:

```python
# Test individual components
from sboxmgr.subscription.validators.protocol_models.enums import LogLevel
from sboxmgr.subscription.validators.protocol_models.transport import WsConfig
from sboxmgr.subscription.validators.protocol_models.protocol_configs import ShadowsocksConfig
```

## Contributing

When adding new protocols or features:

1. **Choose the Right Module**: Place new components in the appropriate module
2. **Follow Patterns**: Use existing patterns for consistency
3. **Add Tests**: Ensure comprehensive test coverage
4. **Update Documentation**: Keep this README updated
5. **Validate Syntax**: Ensure all files pass `py_compile`

## Future Enhancements

- **New Protocols**: Easy to add new protocol support
- **Enhanced Validation**: Additional validation rules
- **Performance Optimization**: Further optimization opportunities
- **Schema Evolution**: Support for schema versioning 