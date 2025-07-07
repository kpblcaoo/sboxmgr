---
name: 🏗️ Subscription Pipeline Architecture
about: Implement new subscription management architecture with plugin system
title: 'feat: Implement subscription pipeline architecture with registry-based plugins'
labels: ['enhancement', 'architecture', 'subscription', 'breaking-change']
assignees: []
---

## 📋 Overview

Implement a new subscription management architecture that replaces the current monolithic approach with a flexible, plugin-based system supporting multiple subscription formats and protocols.

## 🎯 Objectives

### Core Architecture Components
- [ ] **SubscriptionManager** - Central subscription management
- [ ] **Registry-based Plugin System** - Dynamic plugin registration and discovery
- [ ] **ParsedServer Model** - Unified server representation
- [ ] **PipelineContext** - Execution context with trace_id, metadata
- [ ] **PipelineResult** - Standardized result format

### Plugin Types Implementation
- [ ] **BaseFetcher** - HTTP, file://, JSON support with User-Agent
- [ ] **BaseParser** - base64, JSON, Clash YAML, URI lists, tolerant JSON
- [ ] **BaseExporter** - sing-box with full protocol support
- [ ] **BaseSelector** - DefaultSelector with urltest readiness
- [ ] **BasePostProcessor** - DedupPostProcessor, PostProcessorChain
- [ ] **BaseMiddleware** - Logging, TagFilter, Enrich middleware
- [ ] **BaseValidator** - Raw and parsed validation with registry

## 🔧 Technical Requirements

### Fail-Tolerance
- [ ] Implement strict/tolerant execution modes
- [ ] Error accumulation in tolerant mode
- [ ] Partial success handling for multi-subscription scenarios
- [ ] Graceful degradation on plugin failures

### Performance & Reliability
- [ ] In-memory caching with force reload capability
- [ ] Resource limits (2MB fetcher limit, configurable)
- [ ] Thread-safe operations
- [ ] Timeout protection for all operations

### Protocol Support
- [ ] **Modern protocols**: vless, vmess, trojan, shadowsocks
- [ ] **Advanced protocols**: WireGuard, Hysteria2, TUIC
- [ ] **Additional protocols**: ShadowTLS, AnyTLS, Tor, SSH
- [ ] **Legacy compatibility**: Auto-detection of sing-box version

## 📊 Acceptance Criteria

### Functionality
- [ ] All existing subscription formats continue to work
- [ ] New plugin system allows easy extension
- [ ] Performance matches or exceeds current implementation
- [ ] Comprehensive error handling and reporting

### Testing
- [ ] Unit tests for all plugin types (>90% coverage)
- [ ] Integration tests for complete pipeline
- [ ] Edge case coverage for all supported formats
- [ ] Performance benchmarks vs current implementation

### Documentation
- [ ] API documentation with examples
- [ ] Plugin development guide
- [ ] Migration guide from current implementation
- [ ] Architecture decision records (ADR)

## 🔗 Dependencies

- Requires completion of security framework (#TBD)
- Blocks ExclusionManager v2 integration (#TBD)
- Related to CLI/UX improvements (#TBD)

## 💡 Implementation Notes

### Plugin Registry Design
```python
@register("base64")
class Base64Parser(BaseParser):
    def parse(self, data: bytes) -> List[ParsedServer]:
        # Implementation
```

### Context Flow
```python
context = PipelineContext(trace_id="...", mode="production")
result = subscription_manager.process(source, context)
# result.config, result.errors, result.success
```

## 🏷️ Labels
`enhancement` `architecture` `subscription` `breaking-change` `plugins`
