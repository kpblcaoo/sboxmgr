# Profiles

Profiles in SBoxMgr allow you to customize configuration generation, filtering, and export settings using JSON configuration files.

## Overview

A profile is a JSON configuration file that defines:
- Subscription settings and preferences
- Export configuration and routing
- Filtering rules and exclusions
- Custom middleware and postprocessors
- Security policies

## Profile Structure

```json
{
  "id": "my-profile",
  "name": "My Custom Profile",
  "description": "Custom profile for my needs",
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http"],
    "socks_port": 1080,
    "http_port": 8080
  },
  "filter": {
    "exclude_tags": ["blocked"],
    "only_tags": ["premium"],
    "geo_filter": {
      "include": ["US", "CA"],
      "exclude": ["CN", "RU"]
    }
  },
  "routing": {
    "final": "proxy",
    "rules": [
      {
        "domain_suffix": [".ru"],
        "outbound": "direct"
      }
    ]
  }
}
```

## Profile Sections

### Subscription Section

Defines subscription source and settings:

```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30,
    "retries": 3,
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

**Options:**
- `url`: Subscription URL
- `user_agent`: Custom User-Agent header
- `timeout`: Request timeout in seconds
- `retries`: Number of retry attempts
- `headers`: Custom HTTP headers

### Export Section

Configures export behavior and inbound settings:

```json
{
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http", "tun"],
    "socks_port": 1080,
    "socks_listen": "127.0.0.1",
    "http_port": 8080,
    "tun_address": "172.19.0.1/30",
    "final_route": "proxy"
  }
}
```

**Options:**
- `format`: Export format (sing-box)
- `inbound_types`: List of inbound types to enable
- `socks_port`, `http_port`, `tproxy_port`: Port numbers
- `socks_listen`, `http_listen`: Listen addresses
- `tun_address`: TUN interface address
- `final_route`: Final routing destination

### Filter Section

Defines server filtering rules:

```json
{
  "filter": {
    "exclude_tags": ["blocked", "slow"],
    "only_tags": ["premium", "fast"],
    "geo_filter": {
      "include": ["US", "CA"],
      "exclude": ["CN", "RU"]
    }
  }
}
```

**Options:**
- `exclude_tags`: Tags to exclude
- `only_tags`: Tags to include (whitelist)
- `geo_filter`: Geographic filtering rules

### Routing Section

Configures routing rules:

```json
{
  "routing": {
    "final": "proxy",
    "rules": [
      {
        "domain_suffix": [".ru", ".рф"],
        "outbound": "direct"
      },
      {
        "ip_is_private": true,
        "outbound": "direct"
      }
    ]
  }
}
```

## Managing Profiles

### List Profiles

```bash
sboxctl profile list
```

### Apply Profile

```bash
sboxctl profile apply my-profile.json
sboxctl export -u "https://example.com/subscription" --index 1
```

### Validate Profile

```bash
sboxctl profile validate profile.json
```

### Explain Profile

```bash
sboxctl profile explain --name my-profile
```

### Show Profile Differences

```bash
sboxctl profile diff --name profile1 --name profile2
```

## Using Profiles

### With Export Command

```bash
# Apply profile and export
sboxctl profile apply my-profile.json
sboxctl export -u "https://example.com/subscription" --index 1

# Or use profile directly
sboxctl export -u "https://example.com/subscription" --index 1 \
  --inbound-types socks --socks-port 1080
```

### Profile Examples

#### Basic Home Profile
```json
{
  "id": "home",
  "name": "Home Profile",
  "subscription": {
    "url": "https://example.com/subscription"
  },
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks"],
    "socks_port": 1080
  }
}
```

#### Developer Profile
```json
{
  "id": "developer",
  "name": "Developer Profile",
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http"],
    "socks_port": 1080,
    "http_port": 8080
  },
  "filter": {
    "exclude_tags": ["slow"]
  }
}
```

#### Server Profile
```json
{
  "id": "server",
  "name": "Server Profile",
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http", "tproxy"],
    "socks_listen": "0.0.0.0",
    "http_listen": "0.0.0.0",
    "socks_auth": "admin:password"
  },
  "routing": {
    "final": "proxy"
  }
}
```

## Profile Locations

Profiles are typically stored in:
- `~/.config/sboxmgr/profiles/` (Linux/macOS)
- `%APPDATA%\sboxmgr\profiles\` (Windows)
- `./profiles/` (current directory)

## Environment Variables

Set profile-related environment variables:

```bash
# Profile directory
export SBOXMGR_PROFILE_DIR="~/.config/sboxmgr/profiles"

# Default profile
export SBOXMGR_DEFAULT_PROFILE="home"
```

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Subscriptions](subscriptions.md) - Subscription management
- [Configuration](../getting-started/configuration.md) - System configuration
