# ADR-0010: Logging Core Architecture

## Status
Accepted

## Context
Enterprise-grade logging system is required for Stage 3 implementation. The system must support:

1. **Multi-Sink Output**: journald, syslog, stdout with auto-detection
2. **Structured Logging**: JSON format for machine processing
3. **Service Integration**: Seamless systemd and container integration
4. **Trace Correlation**: Request/operation tracing across components
5. **Performance**: Minimal overhead in production environments

## Decision

### Core Architecture: Hybrid Logging System

#### LOG-01: Sink Selection Strategy
**Decision**: Hybrid sink selection with auto-detection and fallback chain

**Strategy**: `auto → journald → syslog → stdout`

```python
from enum import Enum
from typing import List, Optional
import logging
import os

class LogSink(Enum):
    AUTO = "auto"
    JOURNALD = "journald"
    SYSLOG = "syslog"
    STDOUT = "stdout"
    FILE = "file"

def detect_available_sinks() -> List[LogSink]:
    """Detect available logging sinks in order of preference."""
    available = []
    
    # Check for systemd/journald
    if os.getenv("INVOCATION_ID") or os.path.exists("/run/systemd/system"):
        available.append(LogSink.JOURNALD)
    
    # Check for syslog
    if os.path.exists("/dev/log") or os.path.exists("/var/run/syslog"):
        available.append(LogSink.SYSLOG)
    
    # Stdout always available
    available.append(LogSink.STDOUT)
    
    return available

def setup_logging_sinks(config: LoggingConfig) -> List[logging.Handler]:
    """Setup logging handlers based on configuration."""
    handlers = []
    
    if LogSink.AUTO in config.sinks:
        # Auto-detection mode
        available = detect_available_sinks()
        primary_sink = available[0] if available else LogSink.STDOUT
        handlers.append(create_handler(primary_sink, config))
    else:
        # Explicit sink configuration
        for sink in config.sinks:
            try:
                handlers.append(create_handler(LogSink(sink), config))
            except Exception as e:
                # Fallback to stdout if sink fails
                logging.error(f"Failed to setup {sink} handler: {e}")
                handlers.append(create_handler(LogSink.STDOUT, config))
    
    return handlers
```

#### LOG-02: Structured Logging Fields
**Decision**: Basic structured fields with extensible metadata

**Core Fields**:
- `timestamp`: ISO 8601 format
- `level`: Standard logging levels
- `message`: Human-readable message
- `component`: Source component/module
- `operation`: Current operation context
- `trace_id`: Correlation ID for request tracing
- `pid`: Process ID for multi-process debugging

```python
import structlog
from contextvars import ContextVar
from typing import Dict, Any
import uuid
import os

# Context variable for trace ID propagation
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

def get_trace_id() -> str:
    """Get current trace ID or generate new one."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]  # Short trace ID
        trace_id_var.set(trace_id)
    return trace_id

def setup_structured_logging(config: LoggingConfig):
    """Configure structured logging with standard fields."""
    
    def add_standard_fields(logger, method_name, event_dict):
        """Add standard fields to all log entries."""
        event_dict.update({
            'timestamp': structlog.stdlib.add_log_level(logger, method_name, event_dict),
            'component': event_dict.get('component', 'sboxmgr'),
            'operation': event_dict.get('operation', 'unknown'),
            'trace_id': get_trace_id(),
            'pid': os.getpid(),
        })
        return event_dict
    
    processors = [
        structlog.stdlib.filter_by_level,
        add_standard_fields,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

#### LOG-03: Multi-Level Configuration
**Decision**: Global level + per-sink overrides

**Configuration Structure**:
```python
from pydantic import BaseSettings, Field
from typing import Dict, Optional

class LoggingConfig(BaseSettings):
    # Global settings
    level: str = Field(default="INFO", description="Global logging level")
    format: Literal["text", "json"] = Field(default="text")
    
    # Sink configuration
    sinks: List[str] = Field(default=["auto"], description="Logging sinks")
    sink_levels: Dict[str, str] = Field(default={}, description="Per-sink log levels")
    
    # Advanced settings
    max_file_size: int = Field(default=10_000_000, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup files")
    
    class Config:
        env_prefix = "SBOXMGR_LOGGING_"
        env_nested_delimiter = "__"

# Example configuration
config = LoggingConfig(
    level="INFO",
    sinks=["journald", "file"],
    sink_levels={
        "journald": "WARNING",  # Only warnings/errors to journald
        "file": "DEBUG",        # Full debug to file
    }
)
```

### Integration with Configuration System

#### Configuration-Driven Setup
```python
from src.sboxmgr.config import AppConfig
from src.sboxmgr.logging import setup_logging

def initialize_application():
    """Initialize application with configuration-driven logging."""
    config = AppConfig()
    
    # Setup logging based on configuration
    setup_logging(config.logging)
    
    # Get logger for this component
    logger = structlog.get_logger("sboxmgr.main")
    
    # Log with structured context
    logger.info(
        "Application initialized",
        component="main",
        operation="startup",
        service_mode=config.service_mode
    )
```

#### Trace ID Propagation
```python
from contextvars import ContextVar
import structlog

def with_trace_id(trace_id: str):
    """Context manager for trace ID propagation."""
    token = trace_id_var.set(trace_id)
    try:
        yield
    finally:
        trace_id_var.reset(token)

# Usage in Orchestrator
class Orchestrator:
    def process_subscription(self, url: str) -> PipelineResult:
        trace_id = str(uuid.uuid4())[:8]
        
        with with_trace_id(trace_id):
            logger = structlog.get_logger("sboxmgr.orchestrator")
            logger.info(
                "Processing subscription",
                operation="process_subscription",
                url=url
            )
            
            # All nested calls will inherit the trace_id
            result = self.subscription_manager.get_servers(url)
            
            return result
```

### Service Mode Integration

#### Systemd Integration
```python
def setup_service_logging(config: LoggingConfig):
    """Setup logging optimized for systemd service."""
    
    if config.service_mode:
        # Service mode: structured JSON to journald
        config.format = "json"
        config.sinks = ["journald"]
        config.level = "INFO"  # Reduce noise in production
    else:
        # CLI mode: human-readable to stdout
        config.format = "text"
        config.sinks = ["stdout"]
        config.level = "INFO"
    
    setup_logging(config)
```

#### Container Integration
```python
def detect_container_environment() -> bool:
    """Detect if running in container environment."""
    return (
        os.path.exists("/.dockerenv") or
        os.getenv("KUBERNETES_SERVICE_HOST") is not None or
        os.getenv("CONTAINER") == "podman"
    )

def setup_container_logging(config: LoggingConfig):
    """Setup logging optimized for containers."""
    
    if detect_container_environment():
        # Container: JSON to stdout for log aggregation
        config.format = "json"
        config.sinks = ["stdout"]
        
        # Use environment variable for log level
        config.level = os.getenv("LOG_LEVEL", "INFO")
```

## Consequences

### Positive
- **Flexibility**: Multiple output sinks with auto-detection
- **Observability**: Structured logging with trace correlation
- **Integration**: Seamless systemd and container support
- **Performance**: Efficient structured logging with minimal overhead
- **Debugging**: Rich context and trace ID propagation

### Negative
- **Complexity**: Multiple logging backends and configuration
- **Dependencies**: Additional dependencies (structlog, systemd bindings)
- **Learning Curve**: Team needs to understand structured logging

### Neutral
- **Migration**: Existing logging needs gradual migration
- **Storage**: JSON logs consume more space than plain text

## Implementation Plan

### Phase 1: Core Logging (Week 1)
1. Create `src/sboxmgr/logging/` module
2. Implement sink detection and handler creation
3. Setup structured logging with standard fields
4. Add trace ID context variable system

### Phase 2: Configuration Integration (Week 1-2)
1. Integrate with AppConfig system
2. Add per-sink level configuration
3. Implement service mode optimizations
4. Add container environment detection

### Phase 3: Advanced Features (Week 2)
1. Add log rotation and file management
2. Implement performance monitoring
3. Add logging middleware for requests
4. Create debugging utilities

## Acceptance Criteria

### Functional Requirements
- [ ] Auto-detection selects appropriate sink (journald > syslog > stdout)
- [ ] Structured logging includes all standard fields
- [ ] Trace ID propagates across all components
- [ ] Per-sink log level configuration works
- [ ] Service mode optimizes for production logging

### Non-Functional Requirements
- [ ] Logging overhead <5% of total application performance
- [ ] Log rotation prevents disk space issues
- [ ] Graceful fallback when preferred sink unavailable
- [ ] JSON format is valid and parseable

### Testing Requirements
- [ ] Unit tests for sink detection logic
- [ ] Integration tests for structured logging
- [ ] Performance tests for logging overhead
- [ ] Container environment tests

## References
- **Related ADRs**: ADR-0009 (Configuration System), ADR-0011 (Event System)
- **Implementation**: Stage 3 Configuration & Logging Foundation
- **Dependencies**: structlog, systemd-python (optional) 