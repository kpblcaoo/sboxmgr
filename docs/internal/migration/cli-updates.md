# CLI Inbound Parameters

## Overview

Starting from version 1.5.0, sboxmgr supports comprehensive CLI parameters for configuring inbound interfaces directly in the export command. This eliminates the need to create JSON profile files for simple inbound configurations.

## Quick Start

### Basic Usage

```bash
# Simple TUN interface
sboxmgr export --inbound-types tun

# SOCKS proxy on custom port
sboxmgr export --inbound-types socks --socks-port 1080

# Multiple inbounds
sboxmgr export --inbound-types tun,socks,http --socks-port 1080 --http-port 8080
```

### With Authentication

```bash
# SOCKS with authentication
sboxmgr export --inbound-types socks --socks-auth user:password

# HTTP proxy with authentication
sboxmgr export --inbound-types http --http-auth proxy:secret
```

## Available Parameters

### Inbound Types

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--inbound-types` | Comma-separated list of inbound types | None | `tun,socks,http` |

**Supported Types:**
- `tun` - TUN interface for system-level proxy
- `socks` - SOCKS proxy server
- `http` - HTTP proxy server
- `tproxy` - Transparent proxy

### TUN Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--tun-address` | TUN interface address | `198.18.0.1/16` | `10.0.0.1/24` |
| `--tun-mtu` | TUN MTU value | `1500` | `1400` |
| `--tun-stack` | Network stack | `mixed` | `system` |

**Network Stacks:**
- `system` - System network stack
- `gvisor` - gVisor network stack
- `mixed` - Mixed mode (default)

### SOCKS Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--socks-port` | SOCKS proxy port | `1080` | `1080` |
| `--socks-listen` | Bind address | `127.0.0.1` | `0.0.0.0` |
| `--socks-auth` | Authentication (user:pass) | None | `user:password` |

### HTTP Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--http-port` | HTTP proxy port | `8080` | `8080` |
| `--http-listen` | Bind address | `127.0.0.1` | `127.0.0.1` |
| `--http-auth` | Authentication (user:pass) | None | `proxy:secret` |

### TPROXY Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--tproxy-port` | TPROXY port | `7895` | `7895` |
| `--tproxy-listen` | Bind address | `0.0.0.0` | `0.0.0.0` |

### DNS Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--dns-mode` | DNS resolution mode | `system` | `tunnel` |

**DNS Modes:**
- `system` - Use system DNS (default)
- `tunnel` - Route DNS through tunnel
- `off` - Disable DNS resolution

## Examples

### Development Setup

```bash
# Local development with SOCKS proxy
sboxmgr export --inbound-types socks --socks-port 1080 --dry-run
```

### Production Setup

```bash
# Production with TUN interface and custom network
sboxmgr export \
  --inbound-types tun \
  --tun-address 10.0.0.1/24 \
  --tun-mtu 1400 \
  --tun-stack system \
  --dns-mode tunnel
```

### Multi-Interface Setup

```bash
# Multiple interfaces for different use cases
sboxmgr export \
  --inbound-types tun,socks,http \
  --tun-address 198.18.0.1/16 \
  --socks-port 1080 \
  --socks-auth user:password \
  --http-port 8080 \
  --http-auth proxy:secret
```

### Security-Focused Setup

```bash
# Secure setup with localhost binding only
sboxmgr export \
  --inbound-types socks,http \
  --socks-listen 127.0.0.1 \
  --socks-port 1080 \
  --http-listen 127.0.0.1 \
  --http-port 8080
```

## Validation and Error Handling

### Port Validation
- Ports must be between 1024 and 65535
- Invalid ports will cause an error

```bash
# ❌ This will fail
sboxmgr export --inbound-types socks --socks-port 80

# ✅ This will work
sboxmgr export --inbound-types socks --socks-port 1080
```

### Address Validation
- Localhost addresses (127.0.0.1, ::1) are always allowed
- Private network addresses (192.168.x.x) are allowed
- External addresses require explicit configuration

```bash
# ❌ This will fail (external address)
sboxmgr export --inbound-types socks --socks-listen 8.8.8.8

# ✅ This will work (localhost)
sboxmgr export --inbound-types socks --socks-listen 127.0.0.1
```

### Authentication Format
- Must be in format `username:password`
- Invalid format will cause an error

```bash
# ❌ This will fail
sboxmgr export --inbound-types socks --socks-auth invalid

# ✅ This will work
sboxmgr export --inbound-types socks --socks-auth user:password
```

## Integration with Existing Features

### With Dry Run
```bash
sboxmgr export --inbound-types tun --dry-run
```

### With Profile Files
```bash
# CLI parameters take precedence over profile files
sboxmgr export --inbound-types socks --client-profile profile.json
```

### With Other Export Options
```bash
sboxmgr export \
  --inbound-types tun,socks \
  --export-format singbox \
  --output config.json \
  --backup
```

## Migration from JSON Profiles

### Before (JSON Profile)
```json
{
  "inbounds": [
    {
      "type": "socks",
      "listen": "127.0.0.1",
      "port": 1080,
      "options": {
        "users": [{"username": "user", "password": "pass"}]
      }
    }
  ]
}
```

### After (CLI Parameters)
```bash
sboxmgr export \
  --inbound-types socks \
  --socks-listen 127.0.0.1 \
  --socks-port 1080 \
  --socks-auth user:pass
```

## Troubleshooting

### Common Issues

**"Invalid inbound type"**
- Check that the inbound type is supported (tun, socks, http, tproxy)
- Ensure proper comma separation for multiple types

**"Port must be between 1024 and 65535"**
- Use a port number in the valid range
- Avoid privileged ports (1-1023)

**"Bind address must be localhost or private network"**
- Use localhost (127.0.0.1) or private network addresses
- Avoid external IP addresses unless explicitly needed

**"Auth must be in format 'username:password'"**
- Ensure authentication is in the correct format
- Use colon as separator, not other characters

### Debug Mode
```bash
# Enable debug output
sboxmgr export --inbound-types tun --debug 1
```

## Best Practices

### Security
- Use localhost binding (127.0.0.1) when possible
- Implement authentication for public-facing proxies
- Use non-standard ports for better security

### Performance
- Choose appropriate MTU values for TUN interfaces
- Use system stack for better performance
- Consider DNS mode based on your needs

### Maintenance
- Use dry-run mode to test configurations
- Keep configurations simple and documented
- Use version control for complex setups

## See Also

- [Export Command Reference](../cli_reference.md#export)
- [Configuration Profiles](../profiles/README.md)
- [Security Guidelines](../security.md)
- [Troubleshooting Guide](../troubleshooting.md)
