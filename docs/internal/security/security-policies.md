# Security Policies Guide

## Overview

Security Policies in sboxmgr provide comprehensive protection against unsafe configurations, weak encryption, and improper authentication methods. They are designed to be fail-secure by default and highly configurable.

## Available Security Policies

### ProtocolPolicy

**Purpose**: Blocks unsafe protocols and allows only secure ones.

**Default Behavior**:
- **Allowed**: vless, trojan, shadowsocks, hysteria2, tuic
- **Blocked**: http, socks4, socks5 (unencrypted protocols)

**Configuration**:
```python
# Whitelist mode (default)
policy = ProtocolPolicy(
    allowed_protocols=["vless", "trojan", "hysteria2"],
    mode="whitelist"
)

# Blacklist mode
policy = ProtocolPolicy(
    blocked_protocols=["http", "socks4", "socks5"],
    mode="blacklist"
)
```

**Example Results**:
```
❌ ProtocolPolicy: Protocol http not in allowed list
    protocol: http
    allowed_protocols: ['vless', 'trojan', 'shadowsocks', 'hysteria2', 'tuic']

✅ ProtocolPolicy: Protocol vless is allowed
```

### EncryptionPolicy

**Purpose**: Ensures strong encryption methods are used.

**Default Behavior**:
- **Strong**: tls, reality, xtls, aes-256-gcm, chacha20-poly1305
- **Weak**: none, plain, aes-128, rc4
- **Unknown**: allowed (for future-proofing)

**Configuration**:
```python
policy = EncryptionPolicy(
    strong_encryption=["tls", "reality", "aes-256-gcm"],
    weak_encryption=["none", "plain", "aes-128"],
    require_encryption=True
)
```

**Example Results**:
```
❌ EncryptionPolicy: Weak encryption method: none
    encryption: none
    weak_methods: ['none', 'plain', 'aes-128', 'rc4']

✅ EncryptionPolicy: Strong encryption: tls
```

### AuthenticationPolicy

**Purpose**: Validates authentication methods and credential strength.

**Default Behavior**:
- **Allowed Methods**: password, uuid, psk, certificate
- **Min Password Length**: 8 characters
- **Required**: Yes (configurable)

**Configuration**:
```python
policy = AuthenticationPolicy(
    required_auth=True,
    allowed_auth_methods=["password", "uuid"],
    min_password_length=12
)
```

**Example Results**:
```
❌ AuthenticationPolicy: Credentials too short: 5 < 12
    credential_length: 5
    min_length: 12

✅ AuthenticationPolicy: Authentication requirements met
```

## CLI Usage

### List Policies
```bash
# List all policies
sboxctl policy list

# List security policies only
sboxctl policy list --group security

# List with severity filter
sboxctl policy list --severity deny
```

### Test Policies
```bash
# Test with inline JSON
sboxctl policy test --server '{"protocol": "http", "encryption": "none"}'

# Test with JSON file
sboxctl policy test --server server.json

# Test with user context
sboxctl policy test --server server.json --user admin

# Hide warnings
sboxctl policy test --server server.json --no-warnings
```

### Manage Policies
```bash
# Enable/disable policies
sboxctl policy enable ProtocolPolicy
sboxctl policy disable CountryPolicy

# Show system info
sboxctl policy info
```

## Integration Examples

### Basic Server Validation
```python
from sboxmgr.policies import policy_registry, PolicyContext

# Test a server configuration
server = {
    "protocol": "vless",
    "encryption": "tls",
    "password": "strong_password_123",
    "port": 443
}

context = PolicyContext(server=server)
result = policy_registry.evaluate(context)

if result.allowed:
    print("✅ Server configuration is secure")
else:
    print(f"❌ Security violation: {result.reason}")
```

### Custom Policy Configuration
```python
from sboxmgr.policies.security_policy import ProtocolPolicy, EncryptionPolicy

# Create custom security policies
strict_protocol = ProtocolPolicy(
    allowed_protocols=["vless", "hysteria2"],  # Only most secure
    mode="whitelist"
)

strict_encryption = EncryptionPolicy(
    strong_encryption=["tls", "reality"],  # Only strongest
    require_encryption=True
)

# Register custom policies
policy_registry.register(strict_protocol)
policy_registry.register(strict_encryption)
```

## Severity Levels

Policies can return different severity levels:

- **INFO** (✅): Policy passed, no issues
- **WARNING** (⚠️): Policy passed but with concerns
- **DENY** (❌): Policy failed, action blocked

### Example with Warnings
```python
# A policy might return a warning for weak but acceptable encryption
result = policy.evaluate(context)
if result.severity == PolicySeverity.WARNING:
    print(f"⚠️ Warning: {result.reason}")
    # Action is still allowed but logged
```

## Best Practices

1. **Fail-Secure**: Always configure policies to deny by default
2. **Whitelist Approach**: Use whitelist mode for maximum security
3. **Regular Testing**: Test policies against your server configurations
4. **Monitoring**: Log policy decisions for audit purposes
5. **Customization**: Adjust policies based on your security requirements

## Troubleshooting

### Common Issues

**Policy not found**:
```bash
# Check registered policies
sboxctl policy list

# Ensure policy is enabled
sboxctl policy enable PolicyName
```

**Unexpected denials**:
```bash
# Test specific server configuration
sboxctl policy test --server server.json

# Check policy metadata for details
sboxctl policy test --server server.json --warnings
```

**Performance concerns**:
- Policies are designed to be lightweight
- Evaluation stops at first denial
- Use `policy.enabled = False` to disable temporarily
