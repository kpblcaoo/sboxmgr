# CLI Inbound Parameters Usage Examples

This document demonstrates how to use the new CLI parameters for inbound configuration in sboxmgr.

## 🚀 Quick Start

### Basic TUN Interface
```bash
python -m sboxmgr.cli export \
  --url "$SUBSCRIPTION_URL" \
  --inbound-types tun \
  --output tun_config.json
```

### SOCKS Proxy with Authentication
```bash
python -m sboxmgr.cli export \
  --url "$SUBSCRIPTION_URL" \
  --inbound-types socks \
  --socks-port 1080 \
  --socks-auth user:password \
  --output socks_config.json
```

## 🔧 Advanced Configurations

### Multi-Protocol Setup
```bash
python -m sboxmgr.cli export \
  --url "$SUBSCRIPTION_URL" \
  --inbound-types tun,socks,http,tproxy \
  --tun-address "198.18.0.1/16" \
  --tun-mtu 1500 \
  --socks-port 1080 \
  --socks-auth user:pass \
  --http-port 8080 \
  --http-auth proxy:secret \
  --tproxy-port 7895 \
  --dns-mode tunnel \
  --output full_config.json
```

### Router Configuration
```bash
python -m sboxmgr.cli export \
  --url "$SUBSCRIPTION_URL" \
  --inbound-types tproxy \
  --tproxy-port 7895 \
  --tproxy-listen "0.0.0.0" \
  --postprocessors geo_filter \
  --output router_config.json
```

### Development Setup
```bash
python -m sboxmgr.cli export \
  --url "$SUBSCRIPTION_URL" \
  --inbound-types socks,http \
  --socks-port 1080 \
  --socks-listen "127.0.0.1" \
  --http-port 8080 \
  --http-listen "127.0.0.1" \
  --dns-mode system \
  --output dev_config.json
```

## 📋 Parameter Reference

### Inbound Types
- `tun` - TUN interface for system-wide routing
- `socks` - SOCKS5 proxy server
- `http` - HTTP proxy server
- `tproxy` - Transparent proxy (Linux only)

### TUN Parameters
- `--tun-address` - Interface address (default: "198.18.0.1/16")
- `--tun-mtu` - MTU value (default: 1500)
- `--tun-stack` - Network stack: system, gvisor, mixed (default: mixed)

### SOCKS Parameters
- `--socks-port` - Port number (default: 1080)
- `--socks-listen` - Bind address (default: "127.0.0.1")
- `--socks-auth` - Authentication "user:password" (optional)

### HTTP Parameters
- `--http-port` - Port number (default: 8080)
- `--http-listen` - Bind address (default: "127.0.0.1")
- `--http-auth` - Authentication "user:password" (optional)

### TPROXY Parameters
- `--tproxy-port` - Port number (default: 7895)
- `--tproxy-listen` - Bind address (default: "0.0.0.0")

### General Parameters
- `--dns-mode` - DNS mode: system, tunnel, off (default: system)

## 🔒 Security Notes

1. **Default Binding**: SOCKS and HTTP default to localhost (127.0.0.1) for security
2. **External Binding**: Use `--*-listen "0.0.0.0"` only when needed
3. **Port Validation**: All ports must be in range 1024-65535
4. **Authentication**: Always use strong passwords for proxy authentication

## 🎯 Use Cases

### Home User
```bash
# Simple TUN setup for personal use
python -m sboxmgr.cli export \
  --inbound-types tun \
  --tun-address "198.18.0.1/16"
```

### Developer
```bash
# Local proxies for development
python -m sboxmgr.cli export \
  --inbound-types socks,http \
  --socks-port 1080 \
  --http-port 8080
```

### Server Admin
```bash
# Multi-protocol server setup
python -m sboxmgr.cli export \
  --inbound-types socks,http,tproxy \
  --socks-listen "0.0.0.0" \
  --socks-auth admin:secure_password \
  --http-listen "0.0.0.0" \
  --http-auth admin:secure_password \
  --tproxy-port 7895
```

## 🆚 vs JSON Profiles

### Before (JSON Profile)
```json
{
  "inbounds": [
    {
      "type": "tun",
      "options": {
        "tag": "tun-in",
        "address": ["198.18.0.1/16"],
        "mtu": 1500,
        "stack": "mixed"
      }
    }
  ]
}
```

### After (CLI Parameters)
```bash
--inbound-types tun --tun-address "198.18.0.1/16" --tun-mtu 1500 --tun-stack mixed
```

Much simpler! 🎉

## 🔄 Compatibility

- ✅ Works alongside existing `--client-profile` parameter
- ✅ CLI parameters take priority over profile-based config
- ✅ All existing functionality preserved
- ✅ Generated configs are sing-box compatible
