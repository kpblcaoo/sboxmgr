# Configuration

This guide covers configuring SBoxMgr for your needs.

## Overview

SBoxMgr uses a JSON configuration file to define settings for subscriptions, exports, logging, and more.

## Configuration File Location

### Default Locations
- Linux/macOS: `~/.config/sboxmgr/config.json`
- Windows: `%APPDATA%\sboxmgr\config.json`

### Custom Location
Set the `SBOXMGR_CONFIG_FILE` environment variable:
```bash
export SBOXMGR_CONFIG_FILE="/path/to/config.json"
```

## Configuration Structure

```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "SBoxMgr/1.0",
    "timeout": 30,
    "retries": 3
  },
  "export": {
    "format": "sing-box",
    "output_path": "/etc/sing-box/config.json",
    "backup": true,
    "validate": true
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/sboxmgr.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "profiles": {
    "directory": "~/.config/sboxmgr/profiles",
    "default": "default"
  },
  "exclusions": {
    "file": "~/.config/sboxmgr/exclusions.json",
    "auto_save": true
  }
}
```

## Configuration Sections

### Subscription Section

Defines default subscription settings:

```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "SBoxMgr/1.0",
    "timeout": 30,
    "retries": 3,
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

**Options:**
- `url`: Default subscription URL
- `user_agent`: Custom User-Agent header
- `timeout`: Request timeout in seconds
- `retries`: Number of retry attempts
- `headers`: Custom HTTP headers

### Export Section

Configures export behavior:

```json
{
  "export": {
    "format": "sing-box",
    "output_path": "/etc/sing-box/config.json",
    "backup": true,
    "validate": true,
    "pretty": true
  }
}
```

**Options:**
- `format`: Default export format (sing-box, clash, xray)
- `output_path`: Default output file path
- `backup`: Create backup before overwriting
- `validate`: Validate configuration before saving
- `pretty`: Pretty-print JSON output

### Logging Section

Configures logging behavior:

```json
{
  "logging": {
    "level": "INFO",
    "file": "/var/log/sboxmgr.log",
    "max_size": "10MB",
    "backup_count": 5,
    "format": "detailed"
  }
}
```

**Options:**
- `level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `file`: Log file path
- `max_size`: Maximum log file size
- `backup_count`: Number of backup files to keep
- `format`: Log format (simple, detailed)

### Profiles Section

Configures profile management:

```json
{
  "profiles": {
    "directory": "~/.config/sboxmgr/profiles",
    "default": "default",
    "auto_load": true
  }
}
```

**Options:**
- `directory`: Profile files directory
- `default`: Default profile name
- `auto_load`: Automatically load default profile

### Exclusions Section

Configures server exclusions:

```json
{
  "exclusions": {
    "file": "~/.config/sboxmgr/exclusions.json",
    "auto_save": true,
    "backup": true
  }
}
```

**Options:**
- `file`: Exclusions file path
- `auto_save`: Automatically save exclusions
- `backup`: Create backup of exclusions file

## Environment Variables

You can override configuration settings using environment variables:

```bash
# Configuration file
export SBOXMGR_CONFIG_FILE="/path/to/config.json"

# Subscription URL
export SINGBOX_URL="https://example.com/subscription"

# Debug level
export SBOXMGR_DEBUG=2

# Log file
export SBOXMGR_LOG_FILE="/tmp/sboxmgr.log"

# Request timeout
export SBOXMGR_TIMEOUT=60

# SSL verification
export SBOXMGR_SSL_VERIFY=true
```

## Configuration Management

### Generate Configuration

Create a new configuration file:

```bash
# Generate with defaults
sboxctl config generate --output config.json

# Generate from template
sboxctl config generate --template template.json --output config.json

# Generate with custom settings
sboxctl config generate --output config.json --subscription-url "https://example.com/sub"
```

### Validate Configuration

Check configuration file validity:

```bash
# Basic validation
sboxctl config validate --file config.json

# Strict validation
sboxctl config validate --file config.json --strict

# Validate and show errors
sboxctl config validate --file config.json --verbose
```

### Update Configuration

Modify existing configuration:

```bash
# Edit configuration file
sboxctl config edit --file config.json

# Update specific settings
sboxctl config update --file config.json --set subscription.url="https://new-url.com"
```

## Configuration Templates

### Basic Template

```json
{
  "subscription": {
    "url": "YOUR_SUBSCRIPTION_URL",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "output_path": "/etc/sing-box/config.json"
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/sboxmgr.log"
  }
}
```

### Advanced Template

```json
{
  "subscription": {
    "url": "YOUR_SUBSCRIPTION_URL",
    "user_agent": "SBoxMgr/1.0",
    "timeout": 60,
    "retries": 3,
    "headers": {
      "Authorization": "Bearer YOUR_TOKEN"
    }
  },
  "export": {
    "format": "sing-box",
    "output_path": "/etc/sing-box/config.json",
    "backup": true,
    "validate": true,
    "pretty": true
  },
  "logging": {
    "level": "DEBUG",
    "file": "/var/log/sboxmgr.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "profiles": {
    "directory": "~/.config/sboxmgr/profiles",
    "default": "default",
    "auto_load": true
  },
  "exclusions": {
    "file": "~/.config/sboxmgr/exclusions.json",
    "auto_save": true,
    "backup": true
  }
}
```

## Security Considerations

### File Permissions

Set appropriate file permissions:

```bash
# Configuration file
chmod 600 ~/.config/sboxmgr/config.json

# Log file
chmod 644 /var/log/sboxmgr.log

# Profile directory
chmod 700 ~/.config/sboxmgr/profiles
```

### Sensitive Data

Avoid storing sensitive data in configuration files:

```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "headers": {
      "Authorization": "Bearer ${SBOXMGR_TOKEN}"
    }
  }
}
```

Use environment variables for sensitive data:

```bash
export SBOXMGR_TOKEN="your-secret-token"
```

## Troubleshooting

### Configuration Errors

```bash
# Check syntax
cat config.json | jq .

# Validate configuration
sboxctl config validate --file config.json

# Check file permissions
ls -la config.json
```

### Missing Configuration

```bash
# Generate default configuration
sboxctl config generate --output config.json

# Set configuration file path
export SBOXMGR_CONFIG_FILE="/path/to/config.json"
```

## See Also

- [Installation](installation.md) - Installation guide
- [Quick Start](quick-start.md) - Getting started
- [CLI Reference](../user-guide/cli-reference.md) - Command reference
- [Troubleshooting](../user-guide/troubleshooting.md) - Problem solving 