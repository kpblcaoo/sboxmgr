---
name: 🎯 ExclusionManager v2 Enhancement
about: Implement enhanced ExclusionManager with versioning, DI, and audit logging
title: 'feat: Implement ExclusionManager v2 with versioning and dependency injection'
labels: ['enhancement', 'exclusions', 'architecture']
assignees: []
---

## 📋 Overview

Implement ExclusionManager v2 with production-ready features: versioning, dependency injection, audit logging, fail-safe mechanisms, and rich CLI interface.

## 🎯 Core Features

### Versioning & Migration
- [ ] **Automatic versioning** - JSON format with version field
- [ ] **Legacy migration** - Seamless upgrade from v1 format
- [ ] **Forward compatibility** - Handle future versions gracefully
- [ ] **Backward compatibility** - Support for existing exclusions

### Dependency Injection Architecture
- [ ] **Plugin interface** - ExclusionManagerInterface for extensibility
- [ ] **Singleton pattern** - Default instance with custom override
- [ ] **Testability** - Mock-friendly design for unit testing
- [ ] **Configuration injection** - Custom file paths and settings

### Audit & Logging
- [ ] **Full operation tracking** - Add, remove, clear operations
- [ ] **Custom logger support** - Injectable logger instance
- [ ] **Security audit trail** - All exclusion changes logged
- [ ] **Debug information** - Detailed logging for troubleshooting

### Fail-Safe Mechanisms
- [ ] **Corrupted file handling** - Graceful fallback to empty list
- [ ] **JSON parsing errors** - Continue operation with warnings
- [ ] **File system errors** - Robust error handling
- [ ] **Atomic operations** - Thread-safe file operations

## �� Technical Implementation

### Data Model
```python
@dataclass
class ExclusionList:
    version: int = 1
    last_modified: str
    exclusions: List[ExclusionEntry]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExclusionList':
        # Handle versioning and migration
```

### Dependency Injection
```python
class ExclusionManagerInterface(ABC):
    @abstractmethod
    def contains(self, server_id: str) -> bool:
        pass
        
class ExclusionManager(ExclusionManagerInterface):
    @classmethod
    def default(cls) -> 'ExclusionManager':
        # Singleton instance
        
    def __init__(self, file_path: Path, logger: Logger = None):
        # Custom configuration
```

### Rich CLI Interface
```python
# Enhanced CLI commands
sboxctl exclusions --list --json
sboxctl exclusions --add 0,1,2 --reason "Too slow"
sboxctl exclusions --remove server-123,0
sboxctl exclusions --clear
```

## 📊 Enhanced UX Features

### Rich Output
- [ ] **Formatted tables** - Beautiful CLI output with Rich library
- [ ] **JSON export** - Machine-readable format for automation
- [ ] **Color coding** - Status indicators and highlights
- [ ] **Progress indicators** - For bulk operations

### Smart Operations
- [ ] **Wildcard matching** - Pattern-based server selection
- [ ] **Bulk operations** - Add/remove multiple servers
- [ ] **Reason tracking** - Optional reason for each exclusion
- [ ] **Statistics** - Summary of exclusions and operations

### Error Handling
- [ ] **User-friendly messages** - Clear error descriptions
- [ ] **Helpful suggestions** - What to do when operations fail
- [ ] **Validation feedback** - Input validation with guidance
- [ ] **Recovery options** - How to fix common issues

## 📊 Acceptance Criteria

### Functionality
- [ ] All v1 features work without changes
- [ ] New features integrate seamlessly
- [ ] Performance equals or exceeds v1
- [ ] Thread-safe operations

### Testing
- [ ] 24+ unit tests pass (current: 24/24)
- [ ] Integration tests with SubscriptionManager
- [ ] Edge case coverage for all scenarios
- [ ] Performance benchmarks vs v1

### Documentation
- [ ] API documentation with examples
- [ ] Migration guide from v1
- [ ] CLI usage examples
- [ ] Plugin development guide

## 🔗 Integration Points

### SubscriptionManager Integration
```python
# Dependency injection in subscription pipeline
manager = ExclusionManager.default()
subscription_mgr = SubscriptionManager(source, exclusion_manager=manager)
```

### Plugin Extensibility
```python
class GeoIPExclusionManager(ExclusionManagerInterface):
    def contains(self, server_id: str) -> bool:
        server = self.get_server_by_id(server_id)
        return server.country in self.blocked_countries
```

## 🔗 Dependencies

- Requires: Security Framework (#TBD)
- Integrates with: Subscription Pipeline (#TBD)
- Blocks: CLI v2 improvements (#TBD)

## 🏷️ Labels
`enhancement` `exclusions` `architecture` `cli` `dx`
