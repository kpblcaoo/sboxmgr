# CLI Reference

This document provides a comprehensive reference for all SBoxMgr CLI commands and their options.

## Overview

SBoxMgr provides a command-line interface for managing sing-box configurations, subscriptions, and profiles.

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
- `validate`: Validate configuration file
- `dump`: Dump resolved configuration
- `schema`: Generate JSON schema
- `env-info`: Show environment detection

**Examples:**
```bash
# Validate config
sboxctl config validate config.json

# Dump configuration
sboxctl config dump --format json

# Generate schema
sboxctl config schema --output schema.json
```

### Profile Management

#### `sboxctl profile`
Profile management commands.

**Subcommands:**
- `list`: List available profiles
- `apply`: Apply profile to configuration
- `validate`: Validate profile
- `explain`: Explain profile settings
- `diff`: Show differences between profiles
- `switch`: Switch to different profile

**Examples:**
```bash
# List profiles
sboxctl profile list

# Apply profile
sboxctl profile apply profile.json

# Validate profile
sboxctl profile validate profile.json

# Switch profile
sboxctl profile switch work
```

### Policy Management

#### `sboxctl policy`
Policy management commands.

**Subcommands:**
- `list`: List available policies
- `test`: Test policies with context
- `audit`: Audit servers against policies
- `enable`: Enable policies
- `disable`: Disable policies
- `info`: Show policy system information

**Examples:**
```bash
# List policies
sboxctl policy list

# Test policies
sboxctl policy test --profile profile.json

# Audit servers
sboxctl policy audit --url "https://example.com/proxy.json"
```

### Language Management

#### `sboxctl lang`
Language management commands.

**Options:**
- `--set <code>`: Set language (en, ru, de, etc.)
- `--list`: List available languages

**Examples:**
```bash
# Set language
sboxctl lang --set ru

# List languages
sboxctl lang --list
```

### Plugin Development

#### `sboxctl plugin-template`
Generate plugin template.

**Options:**
- `<type>`: Plugin type (fetcher, parser, exporter, validator)
- `<ClassName>`: Class name in CamelCase
- `--output-dir <path>`: Output directory

**Example:**
```bash
sboxctl plugin-template fetcher MyCustomFetcher --output-dir ./plugins/
```

## Environment Variables

- `SBOXMGR_CONFIG_FILE`: Default configuration file path
- `SBOXMGR_LOG_FILE`: Log file path
- `SBOXMGR_EXCLUSION_FILE`: Exclusions file path
- `SBOXMGR_LANG`: Interface language
- `SBOXMGR_DEBUG`: Default debug level

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Validation error
- `4`: Network error
- `5`: Permission error

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

## See Also

- [Profiles](profiles.md) - Working with profiles
- [Subscriptions](subscriptions.md) - Subscription management
- [Troubleshooting](troubleshooting.md) - Problem solving 