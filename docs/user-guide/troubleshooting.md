# Troubleshooting

This guide helps you resolve common issues with SBoxMgr.

## Common Issues

### Network Problems

#### Connection Timeout
**Symptoms:** Commands fail with timeout errors.

**Solutions:**
```bash
# Increase timeout
sboxctl export --url "https://example.com/subscription" --timeout 60

# Check network connectivity
curl -I "https://example.com/subscription"

# Use different DNS
export SBOXMGR_DNS="8.8.8.8"
```

#### SSL/TLS Errors
**Symptoms:** SSL certificate verification failures.

**Solutions:**
```bash
# Disable SSL verification (not recommended for production)
export SBOXMGR_SSL_VERIFY=false

# Update CA certificates
sudo update-ca-certificates
```

### Authentication Issues

#### Invalid Credentials
**Symptoms:** 401/403 errors when accessing subscription.

**Solutions:**
- Verify username/password
- Check API key format
- Ensure proper authentication headers

#### Expired Tokens
**Symptoms:** Authentication works initially but fails later.

**Solutions:**
- Refresh authentication tokens
- Check token expiration
- Update subscription URL with new token

### Parsing Errors

#### Invalid Format
**Symptoms:** "Failed to parse subscription" errors.

**Solutions:**
```bash
# Check subscription format
sboxctl subscription validate --url "https://example.com/subscription"

# View raw data
curl "https://example.com/subscription" | head -20
```

#### Encoding Issues
**Symptoms:** Character encoding problems in server names.

**Solutions:**
- Check subscription encoding (UTF-8 recommended)
- Verify base64 encoding if applicable
- Use proper content-type headers

### Configuration Problems

#### Invalid Configuration
**Symptoms:** "Configuration validation failed" errors.

**Solutions:**
```bash
# Validate configuration
sboxctl config validate --file config.json

# Check configuration syntax
cat config.json | jq .

# Use strict validation
sboxctl config validate --file config.json --strict
```

#### Missing Files
**Symptoms:** "File not found" errors.

**Solutions:**
```bash
# Check file paths
ls -la /path/to/config.json

# Verify permissions
chmod 644 config.json

# Use absolute paths
sboxctl export --config /absolute/path/config.json
```

## Debug Mode

Enable debug output to get detailed information:

```bash
# Level 1: Basic debug info
sboxctl list-servers -d 1

# Level 2: Detailed debug info
sboxctl list-servers -d 2

# Level 3: Verbose debug info
sboxctl list-servers -d 3
```

## Log Files

Check log files for detailed error information:

```bash
# View log file
tail -f /var/log/sboxmgr.log

# Search for errors
grep ERROR /var/log/sboxmgr.log

# Check log file size
ls -lh /var/log/sboxmgr.log
```

## Environment Variables

Common environment variables for troubleshooting:

```bash
# Debug level
export SBOXMGR_DEBUG=3

# Log file path
export SBOXMGR_LOG_FILE="/tmp/sboxmgr.log"

# Configuration file
export SBOXMGR_CONFIG_FILE="/path/to/config.json"

# Request timeout
export SBOXMGR_TIMEOUT=60

# SSL verification
export SBOXMGR_SSL_VERIFY=true
```

## Performance Issues

### Slow Operations
**Symptoms:** Commands take too long to complete.

**Solutions:**
```bash
# Use caching
sboxctl export --cache

# Reduce timeout for faster failure
sboxctl export --timeout 10

# Use local subscription file
sboxctl export --url "file:///path/to/subscription.txt"
```

### High Memory Usage
**Symptoms:** Process uses excessive memory.

**Solutions:**
- Limit number of servers processed
- Use filtering to reduce data size
- Process subscriptions in smaller batches

## Platform-Specific Issues

### Linux
```bash
# Check dependencies
ldd $(which sboxctl)

# Verify Python installation
python3 --version

# Check file permissions
ls -la /usr/local/bin/sboxctl
```

### macOS
```bash
# Check Homebrew installation
brew list | grep sboxmgr

# Verify Python paths
which python3

# Check file permissions
ls -la /usr/local/bin/sboxctl
```

### Windows
```cmd
# Check PATH environment
echo %PATH%

# Verify Python installation
python --version

# Check file permissions
icacls C:\path\to\sboxctl.exe
```

## Getting Help

### Self-Diagnosis
```bash
# Check version
sboxctl --version

# Show help
sboxctl --help

# Validate installation
sboxctl config validate --file /etc/sing-box/config.json
```

### Reporting Issues
When reporting issues, include:
- SBoxMgr version
- Operating system
- Error messages
- Debug output
- Configuration files (sanitized)

### Community Support
- GitHub Issues
- Documentation
- Community forums

## See Also

- [CLI Reference](cli-reference.md) - Command line interface
- [Profiles](profiles.md) - Profile management
- [Subscriptions](subscriptions.md) - Subscription management 