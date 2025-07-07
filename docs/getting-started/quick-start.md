# SBoxMgr Quick Start Guide

## 🚀 Quick Start

```bash
# Basic command
sboxctl export -u "YOUR_SUBSCRIPTION_URL" --index 1

# With parameters
sboxctl export \
  -u "YOUR_SUBSCRIPTION_URL" \
  --index 1 \
  --inbound-types socks \
  --socks-port 1080
```

## 📋 Core Components

| Component | File | Purpose |
|-----------|------|---------|
| CLI Entry | `cli/commands/export.py` | Command parsing, coordination |
| InboundBuilder | `cli/inbound_builder.py` | Create ClientProfile from CLI |
| Fetchers | `subscription/fetchers/` | Load subscriptions (URL/File/API) |
| Parsers | `subscription/parsers/` | Parse formats (YAML/JSON/base64) |
| Middleware | `subscription/middleware/` | Data enrichment |
| Postprocessors | `subscription/postprocessors/` | Filtering and sorting |
| Exporters | `subscription/exporters/` | Generate sing-box config |
| Policies | `policies/` | Security policies |

## 🔄 Data Flow

```
CLI → InboundBuilder → Fetcher → Parser → Middleware → Postprocessors → Exporter → Output
```

## 📝 Available Parameters

### Inbound Types
- `tun` - TUN interface (system routing)
- `socks` - SOCKS5 proxy server
- `http` - HTTP proxy server
- `tproxy` - Transparent proxy (Linux)

### Postprocessors
- `geo_filter` - Filter by countries
- `tag_filter` - Filter by tags
- `latency_sort` - Sort by ping
- `duplicate_removal` - Remove duplicates

### Middleware
- `logging` - Operation logging
- `enrichment` - Metadata enrichment

## 🛡️ Security by Default

- SOCKS/HTTP: bind to `127.0.0.1`
- Ports: only unprivileged (1024-65535)
- TPROXY: bind to `0.0.0.0` (required for functionality)
- Warnings for external bind

## 🔧 Configuration Examples

### Home User
```bash
sboxctl export -u "YOUR_URL" --index 1 --inbound-types tun
```

### Developer
```bash
sboxctl export -u "YOUR_URL" --index 1 \
  --inbound-types socks,http \
  --socks-port 1080 \
  --http-port 8080
```

### Server
```bash
sboxctl export -u "YOUR_URL" --index 1 \
  --inbound-types socks,http,tproxy \
  --socks-listen "0.0.0.0" \
  --socks-auth admin:password \
  --http-listen "0.0.0.0" \
  --postprocessors geo_filter
```

## 🚨 Common Issues

**Q: No servers appear**
```bash
# Add logging
sboxctl export -u "YOUR_URL" --index 1 --middleware logging
```

**Q: Need filtering**
```bash
# Exclude Russian servers
sboxctl export -u "YOUR_URL" --index 1 --postprocessors geo_filter
```

**Q: Bind permission error**
```bash
# Use unprivileged ports
sboxctl export -u "YOUR_URL" --index 1 --socks-port 1080  # not 80
```

**Q: External proxy access**
```bash
# Explicitly bind to all interfaces
sboxctl export -u "YOUR_URL" --index 1 --socks-listen "0.0.0.0"
```

## 📊 Debugging

```bash
# Full logging
sboxctl export -u "YOUR_URL" --index 1 --debug 2

# Check without saving
sboxctl export -u "YOUR_URL" --index 1 --dry-run

# Validate result
sing-box check -c config.json
```

## 🎯 Architectural Principles

1. **Modularity** - Each component is independent
2. **Security** - Secure by default
3. **Extensibility** - Easy to add new formats/protocols
4. **Compatibility** - Backward compatibility with profiles
5. **Validation** - Validation at every level
