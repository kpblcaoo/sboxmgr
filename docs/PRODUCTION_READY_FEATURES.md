# Production-Ready Features

This document describes the production-ready features added to the sing-box exporter for modern sing-box 1.11.0 compatibility.

## Overview

The modern sing-box exporter (`singbox_export()`) now supports advanced features for production use:

1. **Override Final Action** - Customize the final routing action
2. **Exclude Outbounds** - Filter out specific outbound types
3. **Modern Rule Actions** - Use sing-box 1.11.0 rule actions instead of legacy special outbounds

## Features

### 1. Override Final Action

You can override the default final action (`auto`) in routing rules by specifying it in the `ClientProfile`:

```python
from src.sboxmgr.subscription.models import ClientProfile

# Create client profile with custom final action
client_profile = ClientProfile(
    routing={"final": "direct"}  # or "block", "auto", etc.
)

# Export with custom final action
config = singbox_export(servers, client_profile=client_profile)
```

**Available final actions:**
- `"auto"` - Default, uses urltest outbound
- `"direct"` - Direct connection
- `"block"` - Block connection
- Any outbound tag name

### 2. Exclude Outbounds

Filter out specific outbound types from the export:

```python
from src.sboxmgr.subscription.models import ClientProfile

# Create client profile that excludes specific protocols
client_profile = ClientProfile(
    exclude_outbounds=["vmess", "shadowsocks"]
)

# Export without excluded protocols
config = singbox_export(servers, client_profile=client_profile)
```

**Common exclusions:**
- `"vmess"` - Legacy VMess protocol
- `"shadowsocks"` - Legacy Shadowsocks
- `"hysteria"` - Legacy Hysteria (use hysteria2 instead)
- `"anytls"` - Experimental AnyTLS

### 3. Combined Features

You can combine both features in a single `ClientProfile`:

```python
client_profile = ClientProfile(
    routing={"final": "direct"},
    exclude_outbounds=["vmess", "shadowsocks"]
)
```

## Example ClientProfile

```json
{
  "inbounds": [
    {
      "type": "tun",
      "listen": "127.0.0.1",
      "options": {
        "tag": "tun-in",
        "interface_name": "tun0",
        "address": ["198.18.0.1/16"],
        "mtu": 1500,
        "auto_route": true,
        "stack": "system",
        "sniff": true
      }
    }
  ],
  "dns_mode": "system",
  "routing": {
    "final": "direct"
  },
  "exclude_outbounds": [
    "vmess",
    "shadowsocks"
  ],
  "extra": {
    "description": "Production-ready configuration"
  }
}
```

## Migration from Legacy

### Before (Legacy Export)

```python
# Old way - includes legacy special outbounds
config = singbox_export_legacy(servers, routes=None)
# Results in: direct, block, dns-out outbounds + legacy warnings
```

### After (Modern Export)

```python
# New way - modern rule actions, no legacy outbounds
config = singbox_export(servers, client_profile=client_profile)
# Results in: clean config with rule actions, no warnings
```

## Benefits

1. **No Legacy Warnings** - Modern export doesn't trigger sing-box 1.11.0 deprecation warnings
2. **Cleaner Configs** - No unnecessary legacy special outbounds
3. **Better Performance** - Fewer outbounds, faster routing
4. **Future-Proof** - Compatible with upcoming sing-box versions
5. **Flexible Control** - Fine-grained control over routing and exclusions

## Testing

Run the test suite to verify features work correctly:

```bash
# Test override final action
pytest tests/test_modern_export.py::TestModernExport::test_override_final_action -v

# Test exclude outbounds
pytest tests/test_modern_export.py::TestModernExport::test_exclude_outbounds -v

# Test combined features
pytest tests/test_modern_export.py::TestModernExport::test_combined_features -v
```

## CLI Usage

Use the new features via CLI:

```bash
# Export with custom client profile
sboxmgr export --url "your-subscription-url" --client-profile examples/production_ready_features.json

# Or build profile from CLI parameters
sboxmgr export --url "your-subscription-url" --inbound-types tun,socks --dns-mode system
```

## Best Practices

1. **Use Modern Export by Default** - `singbox_export()` is now the default
2. **Exclude Legacy Protocols** - Filter out vmess, shadowsocks for better performance
3. **Customize Final Action** - Use `direct` for local traffic, `block` for security
4. **Test Configurations** - Always validate with `sing-box check`
5. **Document Profiles** - Use `extra.description` to document your configurations 