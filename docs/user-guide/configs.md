# Configurations

Configurations in SBoxMgr allow you to customize configuration generation, filtering, and export settings using TOML or JSON configuration files.

## Overview

A configuration is a TOML (or JSON) file that defines:
- Subscription sources and filtering rules
- Export format and settings
- Routing configuration
- Agent behavior
- UI preferences

## Configuration Structure

```toml
# Basic configuration example
id = "my-config"
description = "My Custom Configuration"
version = "1.0"

# Subscription sources
[[subscriptions]]
id = "main"
enabled = true
priority = 1

# Filtering rules
[filters]
exclude_tags = ["blocked", "slow"]
only_tags = ["premium"]
exclusions = ["bad-server.com"]
only_enabled = true

# Routing configuration
[routing]
default_route = "tunnel"

[routing.custom_routes]
"youtube.com" = "direct"
"github.com" = "direct"

# Export settings
[export]
format = "sing-box"
outbound_profile = "vless-real"
inbound_profile = "tun"
output_file = "config.json"

# Agent settings
[agent]
auto_restart = false
monitor_latency = true
health_check_interval = "30s"
log_level = "info"

# UI preferences
[ui]
default_language = "en"
mode = "cli"
show_debug_info = false
```

## Configuration Sections

### Subscriptions
Define subscription sources and their priorities.

### Filters
Control which servers are included in the final configuration.

### Routing
Configure how traffic is routed through different servers.

### Export
Specify output format and export settings.

### Agent
Configure agent behavior and monitoring.

### UI
Set user interface preferences.

## Managing Configurations

### List Configurations
```bash
sboxctl config list
```

### Apply Configuration
```bash
sboxctl config apply my-config.toml
```

### Switch Active Configuration
```bash
sboxctl config switch work
```

### Show Current Status
```bash
sboxctl config status
```

### Validate Configuration
```bash
sboxctl config validate config.toml
```

### Create New Configuration
```bash
sboxctl config create home --description "Home configuration"
```

### Edit Configuration
```bash
sboxctl config edit home
```

## Using Configurations

### Basic Workflow
```bash
# Create or switch to a configuration
sboxctl config switch home

# Export using active configuration
sboxctl export --url https://example.com/subscription

# Or apply specific configuration
sboxctl config apply my-config.toml
sboxctl export --url https://example.com/subscription
```

### Configuration Examples

#### Basic Home Configuration
```toml
id = "home"
description = "Home Configuration"
version = "1.0"

[[subscriptions]]
id = "main"
enabled = true
priority = 1

[export]
format = "sing-box"
inbound_profile = "tun"
output_file = "home-config.json"

[filters]
exclude_tags = ["slow"]
```

#### Developer Configuration
```toml
id = "developer"
description = "Developer Configuration"
version = "1.0"

[export]
format = "sing-box"
inbound_profile = "socks"
output_file = "dev-config.json"

[filters]
exclude_tags = ["slow"]

[ui]
show_debug_info = true
log_level = "debug"
```

#### Server Configuration
```toml
id = "server"
description = "Server Configuration"
version = "1.0"

[export]
format = "sing-box"
inbound_profile = "tproxy"
output_file = "server-config.json"

[routing]
default_route = "proxy"
```

## Configuration Locations

Configurations are stored in:
- `~/.config/sboxmgr/configs/` (Linux/macOS)
- `%APPDATA%\sboxmgr\configs\` (Windows)
- Custom directory via `--directory` option

## Environment Variables

Set configuration-related environment variables:

```bash
# Configuration directory
export SBOXMGR_CONFIG_DIR="~/.config/sboxmgr/configs"

# Default configuration
export SBOXMGR_DEFAULT_CONFIG="home"
```

## Migration from Profiles

If you have existing JSON profiles, you can migrate them to TOML:

```bash
# Migrate specific file
sboxctl config migrate old-profile.json --target new-config.toml

# The system will automatically use TOML format for new configurations
```

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Subscriptions](subscriptions.md) - Subscription management
- [Configuration](../getting-started/configuration.md) - System configuration
