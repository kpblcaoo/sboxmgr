# Subscriptions

SBoxMgr supports various subscription formats for managing proxy server configurations.

## Overview

Subscriptions provide a way to automatically fetch and update proxy server configurations from remote sources.

## Supported Formats

### Sing-box Format
Native sing-box configuration format.

### Clash Format
Clash configuration format with proxy groups.

### Base64 Encoded
Base64 encoded subscription data.

### URI List
Simple list of proxy URIs.

### JSON Format
Structured JSON subscription data.

## Subscription Sources

### HTTP/HTTPS URLs
```bash
sboxctl export --url "https://example.com/subscription"
```

### Local Files
```bash
sboxctl export --url "file:///path/to/subscription.txt"
```

### API Endpoints
```bash
sboxctl export --url "https://api.example.com/subscription"
```

## Authentication

### Basic Authentication
```bash
sboxctl export --url "https://username:password@example.com/subscription"
```

### Custom Headers
Use profiles to set custom headers:
```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "headers": {
      "Authorization": "Bearer token",
      "X-API-Key": "your-api-key"
    }
  }
}
```

## Subscription Management

### Fetching Data
```bash
# Fetch subscription data
sboxctl subscription fetch --url "https://example.com/subscription"

# Save to file
sboxctl subscription fetch --url "https://example.com/subscription" --output data.json
```

### Listing Servers
```bash
# List all servers
sboxctl list-servers --url "https://example.com/subscription"

# With filtering
sboxctl list-servers --url "https://example.com/subscription" --filter "US"
```

### Validation
```bash
# Validate subscription
sboxctl subscription validate --url "https://example.com/subscription"
```

## Environment Variables

Set default subscription URL:
```bash
export SINGBOX_URL="https://example.com/subscription"
```

Then use without `--url`:
```bash
sboxctl list-servers
```

## Error Handling

### Network Errors
- Automatic retries with exponential backoff
- Configurable timeout settings
- Fallback to cached data if available

### Parsing Errors
- Detailed error messages
- Partial data recovery when possible
- Validation of individual servers

### Authentication Errors
- Clear error messages
- Support for multiple authentication methods
- Retry with different credentials

## Examples

### Basic Usage
```bash
# Export sing-box config
sboxctl export --url "https://example.com/subscription" --format sing-box

# List servers with debug info
sboxctl list-servers --url "https://example.com/subscription" -d 2
```

### Advanced Usage
```bash
# Use profile with custom settings
sboxctl export --profile my-profile --url "https://example.com/subscription"

# Export with routing and filtering
sboxctl export --url "https://example.com/subscription" --routing --filter
```

## Troubleshooting

### Common Issues

**Network Timeout**
```bash
# Increase timeout
sboxctl export --url "https://example.com/subscription" --timeout 60
```

**Authentication Failed**
- Check credentials
- Verify API key format
- Ensure proper headers

**Parsing Errors**
- Check subscription format
- Validate URL accessibility
- Review error logs

### Debug Mode
```bash
# Enable debug output
sboxctl list-servers --url "https://example.com/subscription" -d 3
```

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Profiles](profiles.md) - Profile management
- [Troubleshooting](troubleshooting.md) - Problem solving 