# Test Plan: Subscription Pipeline & Routing Layer

## Coverage Goals
- >=90% coverage required before migration
- Edge-cases: mixed schemes (ss:// as base64 and as URI), query parameters, emoji, comments, broken lines
- For Routing Layer: tests for context, exclusions, user_routes, mode passing

## Rationale
Most subscriptions and routing scenarios in the wild are available in invalid or non-standard form. Parsers and routers must be fail-safe and forward-compatible. Tests should catch errors on broken lines, unexpected parameters, and edge-cases. 