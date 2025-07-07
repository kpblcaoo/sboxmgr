# Event System Guide

## Overview

The sboxmgr Event System provides a comprehensive, thread-safe event-driven architecture for monitoring, debugging, and extending the VPN configuration management system.

## Key Features

- **Thread-Safe**: Concurrent event processing with proper locking
- **Priority-Based**: Events processed by priority (CRITICAL → DEBUG)
- **Filtering**: Advanced event filtering by type, source, payload
- **Statistics**: Real-time event monitoring and statistics collection
- **Decorators**: Simple handler registration via decorators
- **Error Handling**: Comprehensive error tracking and recovery

## Basic Usage

### Emitting Events

```python
from sboxmgr.events import emit_event, EventType, EventPriority

# Simple event emission
event = emit_event(
    EventType.CONFIG_UPDATED,
    {"config_path": "/etc/sboxmgr/config.json", "size": 1024},
    source="config.manager"
)

# High-priority event
event = emit_event(
    EventType.ERROR_OCCURRED,
    {
        "error_type": "ValidationError",
        "error_message": "Invalid configuration",
        "component": "config.validator"
    },
    source="config.validator",
    priority=EventPriority.HIGH
)
```

### Creating Event Handlers

```python
from sboxmgr.events import event_handler, EventType, EventData

@event_handler(EventType.CONFIG_UPDATED, EventType.CONFIG_VALIDATED)
def handle_config_events(event_data: EventData):
    """Handle configuration-related events."""
    print(f"Config event: {event_data.event_type}")
    print(f"Source: {event_data.source}")
    print(f"Payload: {event_data.payload}")

@event_handler(EventType.ERROR_OCCURRED, priority=90)
def handle_errors(event_data: EventData):
    """Handle system errors with high priority."""
    error_type = event_data.get("error_type", "Unknown")
    error_msg = event_data.get("error_message", "No message")
    component = event_data.get("component", event_data.source)

    print(f"ERROR in {component}: {error_type} - {error_msg}")
```

## Event Types

```python
from sboxmgr.events import EventType

# Configuration events
EventType.CONFIG_UPDATED          # Configuration file updated
EventType.CONFIG_VALIDATED        # Configuration validation completed
EventType.CONFIG_GENERATED        # Configuration generated from template

# Agent events
EventType.AGENT_VALIDATION_STARTED    # Agent validation started
EventType.AGENT_VALIDATION_COMPLETED  # Agent validation completed
EventType.AGENT_INSTALLATION_STARTED  # Agent installation started

# Error and debug events
EventType.ERROR_OCCURRED          # System error occurred
EventType.WARNING_ISSUED          # Warning issued
EventType.DEBUG_INFO              # Debug information
```

## Integration Examples

### Configuration Management

```python
@event_handler(EventType.CONFIG_GENERATED)
def log_config_generation(event_data: EventData):
    server_count = event_data.get("server_count", 0)
    outbound_count = event_data.get("outbound_count", 0)
    status = event_data.get("status", "unknown")

    if status == "completed":
        print(f"✅ Generated config with {server_count} servers, {outbound_count} outbounds")
```

### Agent Bridge Integration

```python
@event_handler(EventType.AGENT_VALIDATION_COMPLETED)
def log_agent_validation(event_data: EventData):
    success = event_data.get("success", False)
    client = event_data.get("client_detected", "unknown")

    if success:
        print(f"✅ Agent validation passed for {client}")
    else:
        errors = event_data.get("errors", [])
        print(f"❌ Agent validation failed: {errors}")
```

### Statistics

```python
from sboxmgr.events.debug import get_event_statistics

# Get real-time statistics
stats = get_event_statistics()
print(f"Total events processed: {stats['total_events']}")
print(f"Event counts by type: {stats['event_counts']}")
print(f"Error counts by type: {stats['error_counts']}")
```

## Best Practices

1. **Use Appropriate Event Types**: Choose specific event types over generic ones
2. **Include Relevant Context**: Provide rich payload data for debugging
3. **Handle Errors Gracefully**: Don't let handler errors break the system
4. **Use Appropriate Priorities**: CRITICAL for system errors, DEBUG for trace info

## Testing

```python
def test_config_event_handler():
    manager = EventManager()
    handled_events = []

    @event_handler(EventType.CONFIG_UPDATED, auto_register=False)
    def test_handler(event_data):
        handled_events.append(event_data)

    manager.register_handler(test_handler._event_handler)
    event = manager.emit(EventType.CONFIG_UPDATED, {"test": "data"}, source="test")

    assert event.success
    assert len(handled_events) == 1
```

## Future Extensions

- **Async Handlers**: Future support for async event handlers
- **Event Persistence**: Optional event storage to database
- **Plugin System**: Event-based plugin architecture
- **Webhooks**: HTTP webhook integration for external systems

For more examples, see `tests/test_events.py` and `src/sboxmgr/events/debug.py`.
