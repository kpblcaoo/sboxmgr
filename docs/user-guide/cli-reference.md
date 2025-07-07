# CLI Reference

This document provides a comprehensive reference for all SBoxMgr CLI commands and their options.

## Overview

SBoxMgr provides a command-line interface for managing sing-box configurations, subscriptions, and user configurations.

## Global Options

All commands support these global options:

- `--debug`, `-d <level>`: Set debug level (0-3)
- `--help`, `-h`: Show help message

## Commands

### Server Management

#### `sboxctl list-servers`
List all servers from subscription.

**Options:**
- `-u, --url <url>`: Subscription URL (required)
- `--format <format>`: Output format (table, json, yaml)
- `--filter <filter>`: Filter servers by criteria

**Example:**
```bash
sboxctl list-servers -u "https://example.com/proxy.json"
```

### Export Configuration

#### `sboxctl export`
Export sing-box configuration.

**Options:**
- `-u, --url <url>`: Subscription URL (required)
- `--index <number>`: Server index to use
- `--remarks <name>`: Server name/remarks to use
- `--dry-run`: Validate without writing files
- `--inbound-types <types>`: Inbound types (tun, socks, http, tproxy)
- `--socks-port <port>`: SOCKS proxy port
- `--socks-listen <address>`: SOCKS listen address
- `--socks-auth <user:pass>`: SOCKS authentication
- `--http-port <port>`: HTTP proxy port
- `--http-listen <address>`: HTTP listen address
- `--http-auth <user:pass>`: HTTP authentication
- `--tproxy-port <port>`: TPROXY port
- `--tproxy-listen <address>`: TPROXY listen address
- `--tun-address <cidr>`: TUN interface address
- `--tun-mtu <mtu>`: TUN interface MTU
- `--tun-stack <stack>`: TUN stack (system, gvisor)
- `--dns-mode <mode>`: DNS mode (system, tunnel, off)
- `--final-route <route>`: Final routing destination
- `--exclude-outbounds <types>`: Exclude outbound types

**Examples:**
```bash
# Basic export
sboxctl export -u "https://example.com/proxy.json" --index 1

# With custom inbound
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --inbound-types socks --socks-port 1080

# Dry run
sboxctl export -u "https://example.com/proxy.json" --index 1 --dry-run
```

### Exclusions Management

#### `sboxctl exclusions`
Manage server exclusions.

**Options:**
- `-u, --url <url>`: Subscription URL
- `--add <index>`: Add server to exclusions
- `--remove <index>`: Remove server from exclusions
- `--view`: View current exclusions
- `--clear`: Clear all exclusions

**Examples:**
```bash
# Add server to exclusions
sboxctl exclusions -u "https://example.com/proxy.json" --add 3

# Remove server from exclusions
sboxctl exclusions -u "https://example.com/proxy.json" --remove 3

# View exclusions
sboxctl exclusions --view

# Clear all exclusions
sboxctl exclusions --clear --yes
```

### Configuration Management

#### `sboxctl config`
Configuration management commands.

**Subcommands:**
- `list`: List available configurations
- `create`: Create new configuration
- `apply`: Apply configuration
- `validate`: Validate configuration file
- `migrate`: Convert JSON to TOML format
- `switch`: Switch active configuration
- `edit`: Edit configuration file
- `status`: Show current active configuration

**Examples:**
```bash
# List configurations
sboxctl config list

# Create new configuration
sboxctl config create home --description "Home configuration"

# Switch to configuration
sboxctl config switch work

# Show current status
sboxctl config status

# Apply configuration
sboxctl config apply my-config.toml

# Validate configuration
sboxctl config validate config.toml

# Edit configuration
sboxctl config edit home

# Migrate from JSON to TOML
sboxctl config migrate old-profile.json --target new-config.toml
```

### Language Management

#### `sboxctl lang`
Language management commands.

**Options:**
- `--set <code>`: Set language (en, ru, de, etc.)

**Examples:**
```bash
# Set language
sboxctl lang --set ru

# Show current language
sboxctl lang
```

## Environment Variables

- `SBOXMGR_CONFIG_FILE`: Default configuration file path
- `SBOXMGR_LOG_FILE`: Log file path
- `SBOXMGR_EXCLUSION_FILE`: Exclusions file path
- `SBOXMGR_LANG`: Interface language
- `SBOXMGR_DEBUG`: Default debug level

## See Also

- [Configurations](configs.md) - Working with configurations
- [Subscriptions](subscriptions.md) - Subscription management

## Examples

### Basic Usage

```bash
# List servers from subscription
sboxctl list-servers -u "https://example.com/proxy.json"

# Export sing-box configuration
sboxctl export -u "https://example.com/proxy.json" --index 1

# Select server by name
sboxctl export -u "https://example.com/proxy.json" --remarks "Fast Server"
```

### Advanced Usage

```bash
# Export with routing and filtering
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --final-route proxy --exclude-outbounds block,dns

# Dry run export
sboxctl export -u "https://example.com/proxy.json" --index 1 --dry-run

# Debug mode
sboxctl list-servers -u "https://example.com/proxy.json" -d 2
```

**Subcommands:**
- `
