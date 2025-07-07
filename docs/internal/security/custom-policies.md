# Custom Policies Guide

This guide explains how to create custom policies for sboxmgr to extend the security and filtering capabilities beyond the built-in policies.

## Overview

Custom policies allow you to implement domain-specific rules for server selection, security validation, and access control. They integrate seamlessly with the existing policy framework and can be enabled/disabled through CLI commands.

## Policy Architecture

### Base Policy Class

All custom policies inherit from `BasePolicy`:

```python
from sboxmgr.policies.base import BasePolicy, PolicyResult

class MyCustomPolicy(BasePolicy):
    name = "my_custom_policy"  # Unique identifier
    description = "Description of what this policy does"

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        # Your evaluation logic here
        pass
```

### Policy Context

The `PolicyContext` provides access to:

- **Server**: The server being evaluated
- **Profile**: Current user profile
- **User**: Current user information
- **Metadata**: Additional context data
- **get_server_identifier()**: Helper to get server identification

### Policy Result

Return a `PolicyResult` with:

```python
# Allow the server
return PolicyResult.allow("Server passed custom check")

# Deny the server
return PolicyResult.deny("Server failed custom check", severity="high")

# Warn about the server
return PolicyResult.warn("Server has potential issues", severity="medium")

# Skip evaluation
return PolicyResult.skip("No relevant data to evaluate")
```

## Creating a Custom Policy

### Step 1: Define the Policy Class

```python
# src/sboxmgr/policies/custom/my_policy.py
from typing import Optional
from sboxmgr.policies.base import BasePolicy, PolicyResult, PolicyContext

class MyCustomPolicy(BasePolicy):
    name = "my_custom_policy"
    description = "Custom policy for specific requirements"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.threshold = config.get("threshold", 100) if config else 100

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        server = context.server

        # Your custom logic here
        if not server:
            return PolicyResult.skip("No server to evaluate")

        # Example: Check server latency
        latency = getattr(server, 'latency', None)
        if latency is None:
            return PolicyResult.warn("No latency information available")

        if latency > self.threshold:
            return PolicyResult.deny(
                f"Latency {latency}ms exceeds threshold {self.threshold}ms",
                severity="medium"
            )

        return PolicyResult.allow(f"Latency {latency}ms is acceptable")
```

### Step 2: Register the Policy

Add your policy to the registry:

```python
# src/sboxmgr/policies/__init__.py
from .custom.my_policy import MyCustomPolicy

# Add to the registry
policy_registry.register(MyCustomPolicy())
```

### Step 3: Configure the Policy

Add configuration to your profile:

```json
{
  "policies": {
    "my_custom_policy": {
      "enabled": true,
      "threshold": 150
    }
  }
}
```

## Advanced Policy Features

### Policy Configuration

Policies can accept configuration parameters:

```python
class ConfigurablePolicy(BasePolicy):
    name = "configurable_policy"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        # Extract configuration
        self.allowed_tags = config.get("allowed_tags", []) if config else []
        self.blocked_tags = config.get("blocked_tags", []) if config else []

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        server = context.server
        if not server:
            return PolicyResult.skip("No server to evaluate")

        # Use configuration in evaluation
        tags = getattr(server, 'tags', [])

        for tag in tags:
            if tag in self.blocked_tags:
                return PolicyResult.deny(f"Tag '{tag}' is blocked")

        if self.allowed_tags and not any(tag in self.allowed_tags for tag in tags):
            return PolicyResult.deny("No allowed tags found")

        return PolicyResult.allow("Tags are acceptable")
```

### Policy Metadata

Add metadata to your results for better debugging:

```python
def evaluate(self, context: PolicyContext) -> PolicyResult:
    server = context.server

    # Collect metadata
    metadata = {
        "server_id": getattr(server, 'id', 'unknown'),
        "evaluation_time": time.time(),
        "custom_field": "custom_value"
    }

    # Your evaluation logic...

    return PolicyResult.allow(
        "Server passed check",
        metadata=metadata
    )
```

### Policy Dependencies

Policies can depend on other policies or external data:

```python
class DependentPolicy(BasePolicy):
    name = "dependent_policy"

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        # Check if required data is available
        if not hasattr(context.server, 'required_field'):
            return PolicyResult.skip("Required field not available")

        # Your evaluation logic...
        pass
```

## Testing Custom Policies

### Unit Tests

Create comprehensive tests for your policy:

```python
# tests/unit/test_my_policy.py
import pytest
from sboxmgr.policies.custom.my_policy import MyCustomPolicy
from sboxmgr.policies.base import PolicyContext

class TestMyCustomPolicy:
    def test_policy_allows_good_server(self):
        policy = MyCustomPolicy({"threshold": 100})
        server = MockServer(latency=50)
        context = PolicyContext(server=server)

        result = policy.evaluate(context)
        assert result.allowed
        assert "acceptable" in result.reason

    def test_policy_denies_bad_server(self):
        policy = MyCustomPolicy({"threshold": 100})
        server = MockServer(latency=150)
        context = PolicyContext(server=server)

        result = policy.evaluate(context)
        assert not result.allowed
        assert "exceeds threshold" in result.reason

    def test_policy_warns_no_data(self):
        policy = MyCustomPolicy()
        server = MockServer()  # No latency attribute
        context = PolicyContext(server=server)

        result = policy.evaluate(context)
        assert result.warning
        assert "No latency information" in result.reason
```

### Integration Tests

Test your policy in the full pipeline:

```python
def test_policy_in_subscription_manager():
    # Test that your policy works with the subscription manager
    pass
```

## Best Practices

### 1. Clear Naming and Documentation

- Use descriptive names for policies
- Provide clear descriptions
- Document configuration options

### 2. Graceful Error Handling

- Handle missing data gracefully
- Return appropriate skip/warn results
- Don't crash on unexpected input

### 3. Performance Considerations

- Keep evaluation logic efficient
- Avoid expensive operations in hot paths
- Consider caching if appropriate

### 4. Configuration Validation

- Validate configuration parameters
- Provide sensible defaults
- Document required vs optional parameters

### 5. Logging and Debugging

- Add appropriate logging
- Include relevant metadata
- Make debugging information available

## Example: Complete Custom Policy

Here's a complete example of a custom policy:

```python
import logging
from typing import Optional, List
from sboxmgr.policies.base import BasePolicy, PolicyResult, PolicyContext

logger = logging.getLogger(__name__)

class ServerTagPolicy(BasePolicy):
    """
    Policy that filters servers based on their tags.

    Configuration:
        required_tags: List of tags that must be present
        blocked_tags: List of tags that cause denial
        preferred_tags: List of preferred tags (warnings if missing)
    """

    name = "server_tag_policy"
    description = "Filters servers based on tag requirements"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.required_tags = config.get("required_tags", []) if config else []
        self.blocked_tags = config.get("blocked_tags", []) if config else []
        self.preferred_tags = config.get("preferred_tags", []) if config else []

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        server = context.server
        if not server:
            return PolicyResult.skip("No server to evaluate")

        server_tags = getattr(server, 'tags', [])
        if not server_tags:
            return PolicyResult.warn("Server has no tags")

        # Check for blocked tags
        for tag in server_tags:
            if tag in self.blocked_tags:
                return PolicyResult.deny(
                    f"Server has blocked tag: {tag}",
                    severity="high"
                )

        # Check for required tags
        if self.required_tags:
            missing_required = set(self.required_tags) - set(server_tags)
            if missing_required:
                return PolicyResult.deny(
                    f"Missing required tags: {missing_required}",
                    severity="medium"
                )

        # Check for preferred tags
        warnings = []
        if self.preferred_tags:
            missing_preferred = set(self.preferred_tags) - set(server_tags)
            if missing_preferred:
                warnings.append(f"Missing preferred tags: {missing_preferred}")

        if warnings:
            return PolicyResult.warn(
                "; ".join(warnings),
                severity="low"
            )

        return PolicyResult.allow("Server tags meet all requirements")
```

## CLI Integration

Your custom policy automatically integrates with CLI commands:

```bash
# Enable your policy
sboxmgr policy enable my_custom_policy

# Disable your policy
sboxmgr policy disable my_custom_policy

# Check policy status
sboxmgr policy list

# Audit servers with your policy
sboxmgr policy audit --policy my_custom_policy
```

## Troubleshooting

### Common Issues

1. **Policy not found**: Ensure the policy is properly registered
2. **Configuration errors**: Validate configuration parameters
3. **Performance issues**: Profile your evaluation logic
4. **Unexpected results**: Add logging and metadata for debugging

### Debugging Tips

- Use `sboxmgr policy audit --verbose` to see detailed evaluation
- Check logs for policy evaluation details
- Use metadata to track evaluation state
- Test with various server configurations

## Next Steps

- Review existing policies for patterns and best practices
- Consider contributing your policy back to the community
- Explore advanced features like policy chaining and dependencies
- Implement comprehensive testing for your policies
