# Subscriptions

SBoxMgr supports various subscription formats for managing proxy server configurations.

## Overview

Subscriptions provide a way to automatically fetch and update proxy server configurations from remote sources. SBoxMgr can parse multiple formats and automatically detect the subscription type.

## Supported Formats

### Sing-box Format
Native sing-box configuration format with outbounds and routing rules.

### Clash Format
Clash configuration format with proxy groups and rules.

### Base64 Encoded
Base64 encoded subscription data (common for many providers).

### URI List
Simple list of proxy URIs (vmess://, vless://, etc.).

### JSON Format
Structured JSON subscription data.

## Subscription Sources

### HTTP/HTTPS URLs
```bash
sboxctl list-servers -u "https://example.com/subscription"
sboxctl export -u "https://example.com/subscription" --index 1
```

### Local Files
```bash
sboxctl list-servers -u "file:///path/to/subscription.txt"
sboxctl export -u "file:///path/to/subscription.txt" --index 1
```

### API Endpoints
```bash
sboxctl list-servers -u "https://api.example.com/subscription"
sboxctl export -u "https://api.example.com/subscription" --index 1
```

## Authentication

### Basic Authentication
```bash
sboxctl list-servers -u "https://username:password@example.com/subscription"
```

### Custom Headers
Use environment variables or profiles to set custom headers:
```bash
# Set custom User-Agent
export SBOXMGR_USER_AGENT="Custom User-Agent"

# Use with subscription
sboxctl list-servers -u "https://example.com/subscription"
```

## Subscription Management

### Listing Servers
```bash
# List all servers
sboxctl list-servers -u "https://example.com/subscription"

# With format detection
sboxctl list-servers -u "https://example.com/subscription" --format auto

# With debug info
sboxctl list-servers -u "https://example.com/subscription" -d 2
```

### Exporting Configurations
```bash
# Export basic config
sboxctl export -u "https://example.com/subscription" --index 1

# Export with custom settings
sboxctl export -u "https://example.com/subscription" --index 1 \
  --inbound-types socks --socks-port 1080

# Dry run (validate without saving)
sboxctl export -u "https://example.com/subscription" --index 1 --dry-run
```

### Server Selection
```bash
# Select by index
sboxctl export -u "https://example.com/subscription" --index 5

# Select by name/remarks
sboxctl export -u "https://example.com/subscription" --remarks "Fast Server"
```

## Environment Variables

Set default subscription URL:
```bash
export SBOXMGR_URL="https://example.com/subscription"
```

Then use without `-u`:
```bash
sboxctl list-servers
sboxctl export --index 1
```

## Error Handling

### Network Errors
- Automatic retries with exponential backoff
- Configurable timeout settings (default: 30 seconds)
- Fallback to cached data if available

### Parsing Errors
- Detailed error messages with debug mode
- Partial data recovery when possible
- Validation of individual servers

### Authentication Errors
- Clear error messages
- Support for multiple authentication methods
- Retry with different credentials

## Examples

### Basic Usage
```bash
# List available servers
sboxctl list-servers -u "https://example.com/subscription"

# Export sing-box config
sboxctl export -u "https://example.com/subscription" --index 1

# Start sing-box with generated config
sing-box run -c config.json
```

### Advanced Usage
```bash
# Export with custom inbound
sboxctl export -u "https://example.com/subscription" --index 1 \
  --inbound-types socks,http \
  --socks-port 1080 \
  --http-port 8080

# Export with routing
sboxctl export -u "https://example.com/subscription" --index 1 \
  --final-route proxy \
  --exclude-outbounds block,dns

# Debug subscription parsing
sboxctl list-servers -u "https://example.com/subscription" -d 3
```

## Troubleshooting

### Common Issues

**Network Timeout**
```bash
# Check network connectivity
curl -I "https://example.com/subscription"

# Use different DNS
export SBOXMGR_DNS="8.8.8.8"
```

**Authentication Failed**
- Check credentials in URL
- Verify API key format
- Ensure proper headers

**Parsing Errors**
- Check subscription format
- Validate URL accessibility
- Review error logs with debug mode

**No Servers Found**
```bash
# Enable debug mode
sboxctl list-servers -u "https://example.com/subscription" -d 2

# Check subscription content
curl "https://example.com/subscription" | head -20
```

### Debug Mode
```bash
# Enable debug output
sboxctl list-servers -u "https://example.com/subscription" -d 3

# Check specific format
sboxctl list-servers -u "https://example.com/subscription" --format clash
```

## Subscription Providers

SBoxMgr works with most subscription providers that support:
- Clash configuration format
- Sing-box configuration format
- Base64 encoded subscriptions
- URI lists

Common providers include:
- V2Ray providers
- Clash providers
- Custom proxy services

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Profiles](profiles.md) - Profile management
- [Troubleshooting](troubleshooting.md) - Problem solving
