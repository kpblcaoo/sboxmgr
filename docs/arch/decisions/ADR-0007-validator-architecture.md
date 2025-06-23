# ADR-0007: Validator Architecture and Pipeline Context

## Status
Proposed

## Context
The subscription processing pipeline requires robust validation at multiple stages (raw data, parsed servers, final config) with fail-tolerance, error tracking, and extensibility. Current implementation lacks:

1. **Unified Context**: No tracing/debugging context across pipeline stages
2. **Error Reporting**: Inconsistent error handling and reporting
3. **Multi-level Validation**: Only basic JSON validation exists
4. **Fail-tolerance**: Single subscription failure breaks entire pipeline
5. **Extensibility**: No plugin system for custom validators

## Decision

### Core Architecture Components

#### 1. PipelineContext (@dataclass)
```python
@dataclass
class PipelineContext:
    trace_id: str          # UUID for tracing
    source: str            # Source URL/file
    mode: str              # CLI mode (strict/tolerant)
    user_routes: list      # User-defined routes
    exclusions: list       # Server exclusions
    debug_level: int       # Logging level
    metadata: dict         # Stage-specific data
```

#### 2. Error Reporter System
```python
class ErrorType(Enum):
    VALIDATION = "validation"
    FETCH = "fetch"
    PARSE = "parse"
    PLUGIN = "plugin"
    INTERNAL = "internal"

@dataclass
class PipelineError:
    type: ErrorType
    stage: str
    message: str
    context: dict
    timestamp: datetime
```

#### 3. PipelineResult (@dataclass)
```python
@dataclass
class PipelineResult:
    config: dict
    context: PipelineContext
    errors: list[PipelineError]
    success: bool
    partial_success: bool
```

### Validation Pipeline
```
Raw Data → RawValidator → Parser → ParsedValidator → PostProcessor → FinalValidator → Export
```

#### 4. BaseValidator Interface
```python
class BaseValidator(ABC):
    @abstractmethod
    def validate(self, data: Any, context: PipelineContext) -> ValidationResult:
        pass
    
    @property
    @abstractmethod
    def validator_type(self) -> str:
        pass
```

#### 5. Registry-based Plugin System
- `RAW_VALIDATOR_REGISTRY` - for raw data validation
- `PARSED_VALIDATOR_REGISTRY` - for parsed server validation  
- `MIDDLEWARE_REGISTRY` - for pipeline middleware
- Auto-discovery via decorators and entry points

### Fail-tolerance Modes
- `--strict`: fail-fast on first error
- `--tolerant`: continue-on-error, accumulate errors, partial success

### Security Considerations
- Validator sandboxing and resource limits
- Input sanitization and size limits
- Secure trace_id generation (no sensitive data)
- Error message redaction for sensitive information

## Consequences

### Positive
- **Unified Context**: Single source of truth for pipeline state
- **Error Tracking**: Comprehensive error collection with tracing
- **Fail-tolerance**: Robust handling of subscription failures
- **Extensibility**: Plugin system for custom validators
- **DX**: Better debugging and development experience
- **Security**: Controlled validation with sandboxing

### Negative
- **Complexity**: Additional abstraction layers
- **Performance**: Context passing overhead
- **Memory**: Error accumulation in tolerant mode

### Neutral
- **Migration**: Existing code needs refactoring to use context
- **Testing**: More comprehensive test coverage required

## Implementation Priority

### 🟥 Critical (v1.5.0)
1. PipelineContext and PipelineResult
2. Error Reporter system
3. Fail-tolerance modes (strict/tolerant)
4. Raw validator registry and base classes

### 🟧 Important (v1.5.0)
5. Middleware registry
6. Basic caching system
7. Plugin template generator

### 🟨 Desirable (v2.0+)
8. Advanced metrics and monitoring
9. Sandboxing for user plugins
10. Rollback and atomic operations

## References
- SEC-14 to SEC-17 in sec_checklist.md
- subscription_pipeline.md implementation plan
- Related: ADR-0004 (Plugin Pipeline), ADR-0002 (Plugin Registry)
