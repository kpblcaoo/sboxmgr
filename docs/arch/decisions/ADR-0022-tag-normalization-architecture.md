# ADR-0022: Tag Normalization Architecture

**Date:** 2025-07-06
**Status:** Proposed
**Authors:** Mikhail Stepanov
**Reviewers:** TBD

## Context

During MVP testing, we discovered inconsistent server tag formats across different User-Agent types:

- **SFI User-Agent**: Produces IP-based tags like `"vless-192.142.18.243"`
- **ClashMeta/1.0 User-Agent**: Produces human-readable names like `"🇳🇱 kpblcaoo Nederland-3"`
- **No User-Agent**: Produces mixed formats depending on source

### Root Cause Analysis

The inconsistency stems from different parsers handling tag/name fields differently:

1. **ClashParser** saves the entire proxy object in `meta`, including the `"name"` field
2. **SingBoxParser** only saves specific fields, missing the `"name"` field
3. **Base64Parser** varies based on URI format

Current tag assignment logic in parsers:
- Uses `tag` field if available
- Falls back to generated tags based on protocol and address
- Doesn't consider `name` field from metadata

## Decision

We will implement a **Tag Normalization Middleware** that centralizes tag assignment logic and ensures consistent behavior across all User-Agent types.

### Architecture Changes

1. **Move tag normalization from parsers to middleware**
   - Remove tag generation logic from individual parsers
   - Create dedicated `TagNormalizer` middleware component

2. **Implement priority-based tag selection**
   ```python
   Priority order:
   1. meta['name'] (human-readable from source)
   2. meta['tag'] (explicit tag from source)
   3. tag (parser-generated tag)
   4. address (IP/domain fallback)
   5. protocol-based fallback
   ```

3. **Preserve source metadata**
   - Keep original `name` and `tag` fields in metadata
   - Allow downstream components to access original values

### Implementation Plan

#### Phase 1: Create TagNormalizer Middleware
```python
class TagNormalizer:
    def process_servers(self, servers: List[ServerModel]) -> List[ServerModel]:
        for server in servers:
            server.tag = self._normalize_tag(server)
        return servers

    def _normalize_tag(self, server: ServerModel) -> str:
        # Priority-based tag selection
        if server.meta.get('name'):
            return self._sanitize_tag(server.meta['name'])
        elif server.meta.get('tag'):
            return self._sanitize_tag(server.meta['tag'])
        elif server.tag:
            return server.tag
        elif server.address:
            return f"{server.protocol}-{server.address}"
        else:
            return f"{server.protocol}-{id(server)}"
```

#### Phase 2: Update Parsers
- Remove tag generation logic from `ClashParser`, `SingBoxParser`, `Base64Parser`
- Ensure parsers preserve `name` and `tag` fields in metadata
- Simplify parser logic to focus on protocol-specific parsing

#### Phase 3: Integration
- Add `TagNormalizer` to middleware pipeline
- Position after enrichment but before validation
- Ensure consistent behavior across all User-Agent types

## Benefits

1. **Consistency**: All User-Agent types produce identical tag formats
2. **Maintainability**: Centralized tag logic, easier to test and modify
3. **Flexibility**: Easy to adjust tag priority or add new sources
4. **Backward Compatibility**: Existing configurations continue to work
5. **Testability**: Single component to test tag normalization logic

## Risks and Mitigations

### Risk: Breaking Changes
- **Mitigation**: Implement behind feature flag initially
- **Mitigation**: Comprehensive testing with existing configurations

### Risk: Performance Impact
- **Mitigation**: Minimal overhead (single pass over servers)
- **Mitigation**: Benchmark against current implementation

### Risk: Tag Conflicts
- **Mitigation**: Implement conflict resolution (append suffix)
- **Mitigation**: Validate uniqueness within server set

## Testing Strategy

1. **Unit Tests**
   - Test tag priority logic
   - Test tag sanitization
   - Test conflict resolution

2. **Integration Tests**
   - Test with all User-Agent types
   - Verify identical output for same subscription
   - Test with various subscription formats

3. **Regression Tests**
   - Ensure existing configurations still work
   - Verify no breaking changes in CLI output

## Implementation Timeline

- **Phase 1**: Create TagNormalizer middleware (1-2 days)
- **Phase 2**: Update parsers (1 day)
- **Phase 3**: Integration and testing (1-2 days)
- **Total**: 3-5 days

## Alternatives Considered

### Alternative 1: Fix in Individual Parsers
- **Pros**: Minimal architectural change
- **Cons**: Duplicated logic, harder to maintain, inconsistent behavior

### Alternative 2: Post-processing in Export
- **Pros**: No middleware changes
- **Cons**: Too late in pipeline, export-specific solution

### Alternative 3: Configuration-based Tag Rules
- **Pros**: User-configurable
- **Cons**: Complex configuration, overkill for MVP

## Decision Rationale

The middleware approach provides the best balance of:
- **Architectural cleanliness**: Single responsibility, proper separation
- **Maintainability**: Centralized logic, easier testing
- **Consistency**: Uniform behavior across all code paths
- **Flexibility**: Easy to extend or modify tag logic

## Implementation Notes

- Use feature branch for development: `feature/tag-normalization`
- Implement comprehensive test coverage before merge
- Document tag normalization behavior in user guide
- Consider adding debug logging for tag selection process

## References

- Issue discovered during MVP testing (2025-07-06)
- Related to subscription parsing architecture (ADR-0018)
- Impacts export chain behavior (ADR-0014)
