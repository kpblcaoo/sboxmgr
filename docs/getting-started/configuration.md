# Configuration

This guide covers configuring SBoxMgr for your needs using environment variables and profiles.

## Overview

SBoxMgr uses environment variables and JSON profiles to configure behavior. There's no single configuration file - instead, settings are controlled through environment variables and individual profile files.

## Environment Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SBOXMGR_CONFIG_FILE` | `./config.json` | Output configuration file path |
| `SBOXMGR_LOG_FILE` | `./sboxmgr.log` | Log file path |
| `SBOXMGR_EXCLUSION_FILE` | `./exclusions.json` | Server exclusions file |
| `SBOXMGR_LANG` | `en` | Interface language |
| `SBOXMGR_DEBUG` | `0` | Debug level (0-3) |

### Subscription Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SBOXMGR_URL` | None | Default subscription URL |
| `SBOXMGR_USER_AGENT` | `SBoxMgr/1.4.0` | Custom User-Agent header |
| `SBOXMGR_TIMEOUT` | `30` | Request timeout in seconds |
| `SBOXMGR_RETRIES` | `3` | Number of retry attempts |

### Network Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SBOXMGR_DNS` | System default | DNS server to use |
| `SBOXMGR_SSL_VERIFY` | `true` | SSL certificate verification |
| `SBOXMGR_PROXY` | None | HTTP proxy for requests |

## Setting Environment Variables

### Linux/macOS
```bash
# Add to ~/.bashrc or ~/.zshrc
export SBOXMGR_CONFIG_FILE="$HOME/.config/sboxmgr/config.json"
export SBOXMGR_LOG_FILE="$HOME/.config/sboxmgr/sboxmgr.log"
export SBOXMGR_EXCLUSION_FILE="$HOME/.config/sboxmgr/exclusions.json"
export SBOXMGR_LANG="en"
export SBOXMGR_DEBUG="0"

# Reload shell configuration
source ~/.bashrc
```

### Windows
```cmd
# Set environment variables
set SBOXMGR_CONFIG_FILE=C:\Users\%USERNAME%\AppData\Roaming\sboxmgr\config.json
set SBOXMGR_LOG_FILE=C:\Users\%USERNAME%\AppData\Roaming\sboxmgr\sboxmgr.log
set SBOXMGR_EXCLUSION_FILE=C:\Users\%USERNAME%\AppData\Roaming\sboxmgr\exclusions.json
```

### Using .env File
Create a `.env` file in the project root:
```bash
# .env
SBOXMGR_CONFIG_FILE=./config.json
SBOXMGR_LOG_FILE=./sboxmgr.log
SBOXMGR_EXCLUSION_FILE=./exclusions.json
SBOXMGR_LANG=en
SBOXMGR_DEBUG=0
SBOXMGR_URL=https://example.com/subscription
```

## Profile Configuration

Profiles are JSON files that define subscription, export, and routing settings. See [Profiles](../user-guide/profiles.md) for detailed information.

### Profile Structure
```json
{
  "id": "my-profile",
  "name": "My Profile",
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http"],
    "socks_port": 1080
  },
  "filter": {
    "exclude_tags": ["blocked"],
    "geo_filter": {
      "exclude": ["CN", "RU"]
    }
  }
}
```

## Directory Structure

### Default Directories
```
~/.config/sboxmgr/
├── config.json          # Generated sing-box config
├── sboxmgr.log          # Application logs
├── exclusions.json      # Server exclusions
└── profiles/            # Profile files
    ├── home.json
    ├── work.json
    └── server.json
```

### Creating Directories
```bash
# Create configuration directory
mkdir -p ~/.config/sboxmgr/profiles

# Set permissions
chmod 755 ~/.config/sboxmgr
chmod 644 ~/.config/sboxmgr/profiles/*.json
```

## Configuration Examples

### Basic Setup
```bash
# Set basic environment variables
export SBOXMGR_CONFIG_FILE="$HOME/.config/sboxmgr/config.json"
export SBOXMGR_LOG_FILE="$HOME/.config/sboxmgr/sboxmgr.log"
export SBOXMGR_EXCLUSION_FILE="$HOME/.config/sboxmgr/exclusions.json"

# Use with commands
sboxctl list-servers -u "https://example.com/subscription"
sboxctl export -u "https://example.com/subscription" --index 1
```

### Development Setup
```bash
# Development environment variables
export SBOXMGR_DEBUG="2"
export SBOXMGR_LOG_FILE="./sboxmgr.log"
export SBOXMGR_CONFIG_FILE="./config.json"

# Run with debug output
sboxctl list-servers -u "https://example.com/subscription" -d 2
```

### Production Setup
```bash
# Production environment variables
export SBOXMGR_CONFIG_FILE="/etc/sing-box/config.json"
export SBOXMGR_LOG_FILE="/var/log/sboxmgr.log"
export SBOXMGR_DEBUG="0"
export SBOXMGR_TIMEOUT="60"

# Use with systemd service
sudo systemctl start sing-box
```

## Configuration Validation

### Validate Environment Variables
```bash
# Check if variables are set
echo "Config file: $SBOXMGR_CONFIG_FILE"
echo "Log file: $SBOXMGR_LOG_FILE"
echo "Debug level: $SBOXMGR_DEBUG"
```

### Validate Profile
```bash
# Validate profile file
sboxctl profile validate ~/.config/sboxmgr/profiles/home.json
```