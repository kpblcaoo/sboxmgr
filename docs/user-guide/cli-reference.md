# CLI Reference

This document provides a comprehensive reference for all SBoxMgr CLI commands and their options.

## Overview

SBoxMgr provides a command-line interface for managing sing-box configurations, subscriptions, and profiles.

## Global Options

All commands support these global options:

- `--debug`, `-d <level>`: Set debug level (0-3)
- `--config <path>`: Specify configuration file path
- `--help`, `-h`: Show help message

## Commands

### Configuration Management

#### `sboxctl config generate`
Generate a new configuration file.

**Options:**
- `--output <path>`: Output file path
- `--template <path>`: Template file path
- `--force`: Overwrite existing file

#### `sboxctl config validate`
Validate configuration file.

**Options:**
- `--file <path>`: Configuration file to validate
- `--strict`: Enable strict validation

### Subscription Management

#### `sboxctl subscription list`
List available subscriptions.

#### `sboxctl subscription fetch`
Fetch subscription data.

**Options:**
- `--url <url>`: Subscription URL
- `--format <format>`: Output format (json, yaml, text)
- `--output <path>`: Output file path

### Server Management

#### `sboxctl list-servers`
List all servers from subscription.

**Options:**
- `--url <url>`: Subscription URL
- `--format <format>`: Output format
- `--filter <filter>`: Filter servers
- `--sort <field>`: Sort by field

#### `sboxctl select-server`
Select a server for use.

**Options:**
- `--index <number>`: Server index
- `--tag <tag>`: Server tag
- `--auto`: Auto-select best server

### Export

#### `sboxctl export`
Export configuration.

**Options:**
- `--url <url>`: Subscription URL
- `--format <format>`: Export format (sing-box, clash, xray)
- `--output <path>`: Output file path
- `--profile <path>`: Profile file path
- `--dry-run`: Validate without writing
- `--routing`: Enable routing rules
- `--filter`: Enable filtering

### Profile Management

#### `sboxctl profile list`
List available profiles.

#### `sboxctl profile create`
Create a new profile.

**Options:**
- `--name <name>`: Profile name
- `--template <path>`: Template file
- `--interactive`: Interactive mode

#### `sboxctl profile edit`
Edit an existing profile.

**Options:**
- `--name <name>`: Profile name
- `--editor <editor>`: Text editor to use

### Exclusions

#### `sboxctl exclusions list`
List server exclusions.

#### `sboxctl exclusions add`
Add server exclusion.

**Options:**
- `--id <id>`: Server ID
- `--tag <tag>`: Server tag
- `--reason <reason>`: Exclusion reason

#### `sboxctl exclusions remove`
Remove server exclusion.

**Options:**
- `--id <id>`: Server ID
- `--tag <tag>`: Server tag

### Language

#### `sboxctl lang set`
Set interface language.

**Options:**
- `--lang <code>`: Language code (en, ru, etc.)

#### `sboxctl lang list`
List available languages.

## Examples

### Basic Usage

```bash
# List servers from subscription
sboxctl list-servers

# Export sing-box configuration
sboxctl export --format sing-box --output config.json

# Select server by index
sboxctl select-server --index 0

# Validate configuration
sboxctl config validate --file config.json
```

### Advanced Usage

```bash
# Export with routing and filtering
sboxctl export --routing --filter --format sing-box

# Dry run export
sboxctl export --dry-run --format clash

# Debug mode
sboxctl list-servers -d 2

# Use custom config
sboxctl --config /path/to/config.json export
```

## Environment Variables

- `SBOXMGR_CONFIG_FILE`: Default configuration file path
- `SBOXMGR_DEBUG`: Default debug level
- `SINGBOX_URL`: Default subscription URL
- `SBOXMGR_LOG_FILE`: Log file path

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Validation error
- `4`: Network error
- `5`: Permission error

## See Also

- [Profiles](profiles.md) - Working with profiles
- [Subscriptions](subscriptions.md) - Subscription management
- [Troubleshooting](troubleshooting.md) - Problem solving 