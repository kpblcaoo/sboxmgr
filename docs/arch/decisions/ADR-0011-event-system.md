# ADR-0011: Event System Architecture

## Status
Accepted

## Context
Stage 3 implementation requires event-driven architecture for component decoupling and cross-cutting concerns. The system must support:

1. **Component Decoupling**: Loose coupling between Orchestrator and auxiliary services
2. **Cross-Cutting Concerns**: Audit logging, metrics, notifications
3. **Trace Propagation**: Automatic trace ID propagation across event boundaries
4. **Performance**: Minimal overhead for synchronous in-process events
5. **Extensibility**: Plugin system for custom event handlers

## Decision

### Core Architecture: Lightweight EventBus with pydispatch

#### EVENT-01: Event System Implementation
**Decision**: EventBus with pydispatch (synchronous, in-process)

**Rationale**:
- **Simplicity**: Single-process, synchronous event handling
- **Performance**: No serialization or network overhead
- **Reliability**: No message queue failures or delivery issues
- **Debugging**: Easy to trace event flow in development
- **Dependencies**: Minimal external dependencies

```python
from pydispatch import dispatcher
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from contextvars import ContextVar
import structlog
import uuid
from datetime import datetime

@dataclass
class Event:
    """Base event class with standard fields."""
    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class EventBus:
    """Lightweight event bus using pydispatch."""

    def __init__(self):
        self.logger = structlog.get_logger("sboxmgr.events")

    def emit(self, event: Event) -> None:
        """Emit an event to all registered handlers."""
        self.logger.debug(
            "Event emitted",
            event_type=event.type,
            source=event.source,
            trace_id=event.trace_id,
            component="event_bus",
            operation="emit"
        )

        # Dispatch to all handlers
        dispatcher.send(
            signal=event.type,
            sender=event.source,
            event=event
        )

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe a handler to an event type."""
        dispatcher.connect(handler, signal=event_type)

        self.logger.debug(
            "Event handler subscribed",
            event_type=event_type,
            handler=handler.__name__,
            component="event_bus",
            operation="subscribe"
        )

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe a handler from an event type."""
        dispatcher.disconnect(handler, signal=event_type)

# Global event bus instance
event_bus = EventBus()
```

#### EVENT-02: Trace ID Propagation with ContextVar
**Decision**: ContextVar + auto-generation for trace-ID propagation

**Implementation**:
- **Automatic Propagation**: ContextVar ensures trace ID flows through call stack
- **Event Integration**: Events automatically inherit trace ID from context
- **Manual Override**: Explicit trace ID setting for external requests
- **Logging Integration**: Structured logging automatically includes trace ID

```python
from contextvars import ContextVar
from typing import Optional
import uuid

# Context variable for trace ID
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

def get_trace_id() -> str:
    """Get current trace ID or generate new one."""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]
        trace_id_var.set(trace_id)
    return trace_id

def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context."""
    trace_id_var.set(trace_id)

def with_trace_id(trace_id: Optional[str] = None):
    """Context manager for trace ID scoping."""
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]

    token = trace_id_var.set(trace_id)
    try:
        yield trace_id
    finally:
        trace_id_var.reset(token)

# Enhanced Event class with automatic trace ID
@dataclass
class Event:
    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=get_trace_id)  # Auto-inherit from context
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Event Types and Schemas

#### Core Event Types
```python
from enum import Enum

class EventType(Enum):
    # Subscription events
    SUBSCRIPTION_FETCHED = "subscription.fetched"
    SUBSCRIPTION_PARSED = "subscription.parsed"
    SUBSCRIPTION_VALIDATED = "subscription.validated"
    SUBSCRIPTION_PROCESSED = "subscription.processed"
    SUBSCRIPTION_FAILED = "subscription.failed"

    # Configuration events
    CONFIG_BUILT = "config.built"
    CONFIG_EXPORTED = "config.exported"
    CONFIG_VALIDATED = "config.validated"

    # System events
    APPLICATION_STARTED = "application.started"
    APPLICATION_STOPPED = "application.stopped"
    ERROR_OCCURRED = "error.occurred"

# Event data schemas
@dataclass
class SubscriptionFetchedData:
    url: str
    content_length: int
    content_type: str
    cache_hit: bool = False

@dataclass
class ConfigBuiltData:
    servers_count: int
    rules_count: int
    export_format: str
    file_size: int

# Helper functions for common events
def create_subscription_event(event_type: EventType, url: str, **data) -> Event:
    """Create a subscription-related event."""
    return Event(
        type=event_type.value,
        source="subscription_manager",
        data={"url": url, **data}
    )

def create_config_event(event_type: EventType, **data) -> Event:
    """Create a configuration-related event."""
    return Event(
        type=event_type.value,
        source="config_builder",
        data=data
    )
```

### Integration with Orchestrator

#### Event Emission in Orchestrator
```python
class Orchestrator:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or event_bus
        self.logger = structlog.get_logger("sboxmgr.orchestrator")

    def process_subscription(self, url: str) -> PipelineResult:
        """Process subscription with event emission."""

        with with_trace_id() as trace_id:
            self.logger.info(
                "Processing subscription started",
                url=url,
                operation="process_subscription"
            )

            try:
                # Emit start event
                self.event_bus.emit(Event(
                    type=EventType.SUBSCRIPTION_FETCHED.value,
                    source="orchestrator",
                    data={"url": url, "status": "started"}
                ))

                # Process subscription
                result = self.subscription_manager.get_servers(url)

                # Emit success event
                self.event_bus.emit(Event(
                    type=EventType.SUBSCRIPTION_PROCESSED.value,
                    source="orchestrator",
                    data={
                        "url": url,
                        "servers_count": len(result.servers),
                        "success": result.success
                    }
                ))

                return result

            except Exception as e:
                # Emit error event
                self.event_bus.emit(Event(
                    type=EventType.SUBSCRIPTION_FAILED.value,
                    source="orchestrator",
                    data={
                        "url": url,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                ))
                raise
```

### Cross-Cutting Services

#### Audit Logger
```python
class AuditLogger:
    """Audit logger that reacts to events."""

    def __init__(self, event_bus: EventBus):
        self.logger = structlog.get_logger("sboxmgr.audit")
        self.event_bus = event_bus

        # Subscribe to audit-worthy events
        self.event_bus.subscribe(EventType.SUBSCRIPTION_PROCESSED.value, self.log_subscription)
        self.event_bus.subscribe(EventType.CONFIG_EXPORTED.value, self.log_config_export)
        self.event_bus.subscribe(EventType.ERROR_OCCURRED.value, self.log_error)

    def log_subscription(self, event: Event) -> None:
        """Log subscription processing for audit trail."""
        self.logger.info(
            "Subscription processed",
            **event.data,
            trace_id=event.trace_id,
            component="audit",
            operation="subscription_audit"
        )

    def log_config_export(self, event: Event) -> None:
        """Log configuration export for audit trail."""
        self.logger.info(
            "Configuration exported",
            **event.data,
            trace_id=event.trace_id,
            component="audit",
            operation="config_audit"
        )

    def log_error(self, event: Event) -> None:
        """Log errors for audit trail."""
        self.logger.error(
            "Error occurred",
            **event.data,
            trace_id=event.trace_id,
            component="audit",
            operation="error_audit"
        )
```

#### Metrics Collector
```python
from collections import defaultdict, Counter
from typing import Dict
import time

class MetricsCollector:
    """Collect metrics from events."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.counters: Dict[str, Counter] = defaultdict(Counter)
        self.timers: Dict[str, list] = defaultdict(list)

        # Subscribe to metric events
        self.event_bus.subscribe(EventType.SUBSCRIPTION_PROCESSED.value, self.record_subscription)
        self.event_bus.subscribe(EventType.SUBSCRIPTION_FAILED.value, self.record_failure)

    def record_subscription(self, event: Event) -> None:
        """Record subscription processing metrics."""
        self.counters['subscriptions']['processed'] += 1
        self.counters['subscriptions']['servers'] += event.data.get('servers_count', 0)

    def record_failure(self, event: Event) -> None:
        """Record failure metrics."""
        self.counters['failures'][event.data.get('error_type', 'unknown')] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return {
            'counters': dict(self.counters),
            'timers': dict(self.timers)
        }
```

## Consequences

### Positive
- **Decoupling**: Components interact through events, not direct dependencies
- **Extensibility**: Easy to add new event handlers without modifying core code
- **Observability**: Comprehensive event logging and metrics collection
- **Trace Correlation**: Automatic trace ID propagation across all events
- **Performance**: Minimal overhead for in-process synchronous events

### Negative
- **Complexity**: Additional abstraction layer for simple operations
- **Debugging**: Event flow can be harder to trace than direct calls
- **Error Handling**: Event handler failures need careful consideration

### Neutral
- **Testing**: Need to mock event bus for unit tests
- **Documentation**: Event schemas and flows need documentation

## Implementation Plan

### Phase 1: Core Event System (Week 1)
1. Create `src/sboxmgr/events/` module
2. Implement EventBus with pydispatch
3. Add Event base class and common event types
4. Implement trace ID context variable system

### Phase 2: Orchestrator Integration (Week 1-2)
1. Add event emission to Orchestrator
2. Update SubscriptionManager to emit events
3. Create audit logger service
4. Add metrics collector service

### Phase 3: Advanced Features (Week 2)
1. Add event filtering and routing
2. Implement event replay for debugging
3. Add performance monitoring for event handlers
4. Create event schema validation

## Acceptance Criteria

### Functional Requirements
- [ ] Events are emitted for all major operations
- [ ] Trace ID propagates automatically through ContextVar
- [ ] Audit logger captures all significant events
- [ ] Metrics collector tracks key performance indicators
- [ ] Event handlers can be added/removed dynamically

### Non-Functional Requirements
- [ ] Event emission overhead <1ms per event
- [ ] Memory usage for event history <10MB
- [ ] Event handler failures don't crash main application
- [ ] Trace ID is unique and properly formatted

### Testing Requirements
- [ ] Unit tests for EventBus functionality
- [ ] Integration tests for event emission and handling
- [ ] Performance tests for event throughput
- [ ] Trace ID propagation tests

## References
- **Related ADRs**: ADR-0009 (Configuration System), ADR-0010 (Logging Core)
- **Implementation**: Stage 3 Configuration & Logging Foundation
- **Dependencies**: pydispatch, structlog
