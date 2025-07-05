# Profiles

Profiles in SBoxMgr allow you to customize configuration generation, filtering, and export settings.

## Overview

A profile is a JSON configuration file that defines:
- Subscription settings
- Export preferences
- Filtering rules
- Routing configuration
- Custom middleware

## Profile Structure

```json
{
  "id": "my-profile",
  "name": "My Custom Profile",
  "description": "Custom profile for my needs",
  "priority": 1,
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "routing": true,
    "filtering": true
  },
  "filter": {
    "exclude_tags": ["blocked"],
    "only_tags": ["premium"],
    "exclusions": ["server-id-1"]
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
    "retries": 3
  }
}
```

**Options:**
- `url`: Subscription URL
- `user_agent`: Custom User-Agent header
- `timeout`: Request timeout in seconds
- `retries`: Number of retry attempts

### Export Section

Configures export behavior:

```json
{
  "export": {
    "format": "sing-box",
    "routing": true,
    "filtering": true,
    "middleware": ["logging", "enrichment"]
  }
}
```

**Options:**
- `format`: Export format (sing-box, clash, xray)
- `routing`: Enable routing rules
- `filtering`: Enable server filtering
- `middleware`: List of middleware to apply

### Filter Section

Defines server filtering rules:

```json
{
  "filter": {
    "exclude_tags": ["blocked", "slow"],
    "only_tags": ["premium", "fast"],
    "exclusions": ["server-id-1", "server-id-2"],
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
- `exclusions`: Server IDs to exclude
- `geo_filter`: Geographic filtering

## Creating Profiles

### Interactive Mode

```bash
sboxctl profile create --interactive
```

This will guide you through profile creation step by step.

### From Template

```bash
sboxctl profile create --name my-profile --template template.json
```

### Manual Creation

Create a JSON file with the profile structure and save it to the profiles directory.

## Managing Profiles

### List Profiles

```bash
sboxctl profile list
```

### Edit Profile

```bash
sboxctl profile edit --name my-profile
```

### Validate Profile

```bash
sboxctl profile validate --name my-profile
```

## Using Profiles

### With Export Command

```bash
sboxctl export --profile my-profile
```

### With List Servers

```bash
sboxctl list-servers --profile my-profile
```

## Profile Priority

Profiles have a priority field that determines which profile to use when multiple profiles match:

- Higher priority numbers take precedence
- Default priority is 1
- Profiles with the same priority use the first one found

## Profile Inheritance

Profiles can inherit from other profiles:

```json
{
  "id": "child-profile",
  "inherits": "parent-profile",
  "export": {
    "format": "clash"
  }
}
```

The child profile will inherit all settings from the parent and override specified fields.

## Examples

### Basic Profile

```json
{
  "id": "basic",
  "name": "Basic Profile",
  "subscription": {
    "url": "https://example.com/subscription"
  },
  "export": {
    "format": "sing-box"
  }
}
```

### Advanced Profile

```json
{
  "id": "advanced",
  "name": "Advanced Profile",
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "SBoxMgr/1.0",
    "timeout": 60
  },
  "export": {
    "format": "sing-box",
    "routing": true,
    "filtering": true,
    "middleware": ["logging", "enrichment"]
  },
  "filter": {
    "exclude_tags": ["blocked"],
    "only_tags": ["premium"],
    "geo_filter": {
      "include": ["US", "CA", "EU"]
    }
  }
}
```

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Subscriptions](subscriptions.md) - Subscription management
- [Troubleshooting](troubleshooting.md) - Problem solving 