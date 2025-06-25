# ADR-0009: Configuration System Architecture

## Status
Accepted

## Context
Stage 3 implementation requires comprehensive configuration management for enterprise deployment. The system must support:

1. **Hierarchical Configuration**: CLI flags > env vars > config.toml > defaults
2. **Service Mode Detection**: Auto-detection between CLI and daemon modes
3. **Validation**: Type-safe configuration with clear error messages
4. **Logging Integration**: Configuration must drive logging subsystem
5. **Enterprise Features**: Environment-based configuration for containers/systemd

## Decision

### Core Architecture: Pydantic BaseSettings

#### CONFIG-01: Configuration Framework
**Decision**: Use Pydantic BaseSettings with `env_nested_delimiter="__"`

**Rationale**:
- Type-safe configuration with automatic validation
- Built-in environment variable support with nested delimiter
- JSON schema auto-generation for documentation
- Integration with FastAPI ecosystem (future web UI)
- Excellent error messages for validation failures

```python
from pydantic import BaseSettings, Field
from typing import Optional, Literal

class LoggingConfig(BaseSettings):
    level: str = Field(default="INFO", description="Logging level")
    format: Literal["text", "json"] = Field(default="text")
    sinks: list[str] = Field(default=["auto"], description="Output sinks")
    
    class Config:
        env_prefix = "SBOXMGR_LOGGING_"
        env_nested_delimiter = "__"

class AppConfig(BaseSettings):
    service_mode: bool = Field(default=False, description="Service daemon mode")
    config_file: Optional[str] = Field(default=None, description="Config file path")
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        env_nested_delimiter = "__"
        env_file = ".env"
```

#### CONFIG-02: Service Mode Detection
**Decision**: Hybrid auto-detection with explicit override

**Strategy**:
1. **Explicit flag**: `--service` or `--daemon` CLI flag
2. **Environment detection**: Check `INVOCATION_ID` (systemd)
3. **Process detection**: Parent process analysis
4. **Default**: CLI mode if uncertain

```python
def detect_service_mode() -> bool:
    # Explicit override
    if "--service" in sys.argv or "--daemon" in sys.argv:
        return True
    
    # Systemd detection
    if os.getenv("INVOCATION_ID"):
        return True
        
    # Container detection
    if os.path.exists("/.dockerenv") or os.getenv("KUBERNETES_SERVICE_HOST"):
        return True
        
    return False
```

#### CONFIG-03: Configuration Validation
**Decision**: Pydantic models + custom validators + auto-generated JSON schema

**Implementation**:
- **Type Safety**: Pydantic ensures type correctness at runtime
- **Custom Validators**: Business logic validation (file paths, URL formats)
- **Schema Generation**: Auto-generate JSON schema for documentation
- **Error Context**: Rich error messages with field-level details

```python
from pydantic import validator, Field
from pathlib import Path

class AppConfig(BaseSettings):
    @validator('config_file')
    def validate_config_file(cls, v):
        if v and not Path(v).exists():
            raise ValueError(f"Config file not found: {v}")
        return v
    
    @validator('logging')
    def validate_logging_config(cls, v):
        if v.level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError(f"Invalid log level: {v.level}")
        return v
```

### Configuration Hierarchy

#### Priority Order (Highest to Lowest)
1. **CLI Arguments**: `--log-level=DEBUG`
2. **Environment Variables**: `SBOXMGR__LOGGING__LEVEL=DEBUG`
3. **Config File**: `config.toml` or `~/.config/sboxmgr/config.toml`
4. **Defaults**: Built-in sensible defaults

#### Environment Variable Mapping
```bash
# Nested configuration via double underscore
SBOXMGR__LOGGING__LEVEL=DEBUG
SBOXMGR__LOGGING__FORMAT=json
SBOXMGR__LOGGING__SINKS=journald,stdout

# Service mode
SBOXMGR__SERVICE_MODE=true
```

### Integration Points

#### Orchestrator Integration
```python
class Orchestrator:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or AppConfig()
        self._setup_logging()
        
    def _setup_logging(self):
        # Configure logging based on config
        setup_logging(self.config.logging)
```

#### CLI Integration
```python
@click.command()
@click.option('--config', help='Configuration file path')
@click.option('--log-level', help='Logging level')
@click.option('--service', is_flag=True, help='Run in service mode')
def main(config, log_level, service):
    # Build configuration from CLI args
    app_config = AppConfig(
        config_file=config,
        service_mode=service,
        logging=LoggingConfig(level=log_level) if log_level else None
    )
```

## Consequences

### Positive
- **Type Safety**: Runtime validation prevents configuration errors
- **Documentation**: Auto-generated schemas and help text
- **Flexibility**: Multiple configuration sources with clear precedence
- **Enterprise Ready**: Environment-based configuration for deployment
- **Development Experience**: Rich error messages and IDE support

### Negative
- **Complexity**: Additional dependency on Pydantic
- **Learning Curve**: Team needs to understand BaseSettings patterns
- **Migration**: Existing configuration needs refactoring

### Neutral
- **Performance**: Minimal overhead for configuration loading
- **Compatibility**: Backward compatible with existing CLI patterns

## Implementation Plan

### Phase 1: Core Configuration (Week 1)
1. Create `src/sboxmgr/config/` module
2. Implement `AppConfig` and `LoggingConfig` classes
3. Add service mode detection logic
4. Create configuration loading utilities

### Phase 2: CLI Integration (Week 1-2)
1. Update CLI commands to use AppConfig
2. Add `--dump-config` command for debugging
3. Integrate with Orchestrator dependency injection
4. Add configuration validation on startup

### Phase 3: Documentation (Week 2)
1. Generate JSON schema from Pydantic models
2. Create configuration examples and templates
3. Document environment variable patterns
4. Add troubleshooting guide

## Acceptance Criteria

### Functional Requirements
- [ ] Configuration loads from all sources (CLI, env, file, defaults)
- [ ] Service mode auto-detection works correctly
- [ ] Validation errors provide clear, actionable messages
- [ ] `--dump-config` outputs final resolved configuration in YAML
- [ ] Environment variables follow `SBOXMGR__SECTION__KEY` pattern

### Non-Functional Requirements
- [ ] Configuration loading takes <100ms
- [ ] Memory usage increase <5MB for configuration system
- [ ] 100% backward compatibility with existing CLI flags
- [ ] JSON schema generation works for documentation

### Testing Requirements
- [ ] Unit tests for all configuration classes
- [ ] Integration tests for hierarchy resolution
- [ ] Environment variable parsing tests
- [ ] Service mode detection tests across platforms

## References
- **Related ADRs**: ADR-0010 (Logging Core), ADR-0011 (Event System)
- **Implementation**: Stage 3 Configuration & Logging Foundation
- **Dependencies**: Pydantic, Click, PyYAML 