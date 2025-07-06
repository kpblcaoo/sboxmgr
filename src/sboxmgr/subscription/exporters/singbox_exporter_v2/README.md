# Sing-box Exporter V2 Module

This module provides a modern sing-box configuration exporter using modular Pydantic models for better validation, type safety, and maintainability.

## Architecture

The module follows the Single Responsibility Principle (SRP) by separating concerns into specialized modules:

### 📁 Module Structure

```
singbox_exporter_v2/
├── __init__.py             # Package exports and public API
├── converter.py            # Main conversion logic
├── protocol_converters.py  # Protocol-specific converters
├── utils.py                # Utility functions for TLS and transport
├── inbound_converter.py    # Inbound configuration conversion
├── exporter.py             # Main exporter class
└── README.md              # This documentation
```

### 📋 Module Responsibilities

| Module | Responsibility | Key Components |
|--------|----------------|----------------|
| `converter.py` | Main conversion coordination | `convert_parsed_server_to_outbound()` |
| `protocol_converters.py` | Protocol-specific conversion logic | `convert_*()` functions for each protocol |
| `utils.py` | Utility functions | `convert_tls_config()`, `convert_transport_config()` |
| `inbound_converter.py` | Inbound configuration handling | `convert_client_profile_to_inbounds()` |
| `exporter.py` | Main exporter class | `SingboxExporterV2` class |

## Supported Protocols

- **Shadowsocks**: SOCKS5 proxy with various encryption methods
- **VMess**: V2Ray protocol with transport layer options
- **VLESS**: Xray protocol with XTLS support
- **Trojan**: TLS-based proxy protocol
- **WireGuard**: Modern VPN protocol
- **Hysteria2**: High-performance UDP-based protocol
- **TUIC**: QUIC-based proxy protocol
- **ShadowTLS**: TLS camouflage protocol
- **AnyTLS**: Flexible TLS proxy
- **Tor**: Tor network proxy
- **SSH**: SSH tunnel protocol
- **HTTP**: HTTP proxy protocol
- **SOCKS**: SOCKS proxy protocol
- **Direct**: Direct connection

## Usage Examples

### Basic Exporter Usage

```python
from sboxmgr.subscription.exporters.singbox_exporter_v2 import SingboxExporterV2

# Create exporter instance
exporter = SingboxExporterV2()

# Export servers to JSON configuration
config_json = exporter.export(servers, client_profile=None)
```

### Single Server Conversion

```python
from sboxmgr.subscription.exporters.singbox_exporter_v2 import convert_parsed_server_to_outbound

# Convert a single ParsedServer to outbound configuration
outbound = convert_parsed_server_to_outbound(server)
```

### Protocol-Specific Conversion

```python
from sboxmgr.subscription.exporters.singbox_exporter_v2 import (
    convert_shadowsocks, convert_vmess, convert_trojan
)

# Convert specific protocols
shadowsocks_outbound = convert_shadowsocks(server, base_data)
vmess_outbound = convert_vmess(server, base_data)
trojan_outbound = convert_trojan(server, base_data)
```

### Inbound Configuration

```python
from sboxmgr.subscription.exporters.singbox_exporter_v2 import convert_client_profile_to_inbounds

# Convert client profile to inbound configurations
inbounds = convert_client_profile_to_inbounds(client_profile)
```

## Key Features

### 🔧 Modern Pydantic Models
- **Full Validation**: Uses sboxmgr.models.singbox Pydantic models
- **Type Safety**: Complete type checking and validation
- **Error Handling**: Detailed error messages for invalid configurations

### 🏗️ Modular Architecture
- **Single Responsibility**: Each module has a clear, focused purpose
- **Reusability**: Components can be used independently
- **Maintainability**: Easy to modify and extend individual protocols

### 📊 Protocol Support
- **Comprehensive**: Supports all major proxy protocols
- **Extensible**: Easy to add new protocol support
- **Validation**: Protocol-specific validation for each type

### 🔄 Conversion Pipeline
- **ParsedServer → Outbound**: Converts subscription data to sing-box format
- **ClientProfile → Inbounds**: Handles local proxy configuration
- **Full Configuration**: Generates complete sing-box configs

## Comparison with Legacy Exporter

| Aspect | Legacy Exporter | V2 Exporter |
|--------|----------------|-------------|
| **Models** | Dict-based validation | Full Pydantic models |
| **Type Safety** | Basic | Complete with type hints |
| **Validation** | Manual checks | Automatic Pydantic validation |
| **Error Handling** | Basic | Detailed error messages |
| **Modularity** | Monolithic | Highly modular |
| **Maintainability** | Difficult | Easy to maintain |
| **Protocol Support** | Legacy approach | Modern sing-box format |
| **Performance** | Good | Better with validation |

## Error Handling

The module provides comprehensive error handling:

```python
try:
    outbound = convert_parsed_server_to_outbound(server)
except ValueError as e:
    print(f"Conversion error: {e}")
```

## Dependencies

- `pydantic`: Core validation framework
- `typing`: Type hints and unions
- `sboxmgr.models.singbox`: Sing-box Pydantic models
- `logging`: Error and debug logging

## Migration from Original File

This module replaces the original `singbox_exporter_v2.py` file (597 lines) with a modular architecture:

- **Before**: Single 597-line file with all functionality
- **After**: 5 specialized modules with clear responsibilities
- **Benefits**: Better maintainability, easier testing, improved organization

## Performance Considerations

- **Lazy Loading**: Modules are loaded only when needed
- **Efficient Validation**: Pydantic's optimized validation
- **Memory Usage**: Reduced memory footprint through modular design
- **Error Recovery**: Graceful handling of conversion failures

## Testing

Each module can be tested independently:

```python
# Test individual converters
from sboxmgr.subscription.exporters.singbox_exporter_v2.protocol_converters import convert_shadowsocks

# Test utilities
from sboxmgr.subscription.exporters.singbox_exporter_v2.utils import convert_tls_config

# Test main exporter
from sboxmgr.subscription.exporters.singbox_exporter_v2 import SingboxExporterV2
```

## Contributing

When adding new protocols or features:

1. **Choose the Right Module**: Place new functionality in the appropriate module
2. **Follow Patterns**: Use existing patterns for consistency
3. **Add Tests**: Ensure comprehensive test coverage
4. **Update Documentation**: Keep this README updated
5. **Validate Syntax**: Ensure all files pass `py_compile`

## Future Enhancements

- **New Protocols**: Easy to add new protocol support
- **Enhanced Validation**: Additional validation rules
- **Performance Optimization**: Further optimization opportunities
- **Configuration Templates**: Pre-built configuration templates
