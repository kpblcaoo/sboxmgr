"""Event system for sboxmgr.

This module provides a comprehensive event system for configuration updates,
service notifications, and plugin hooks. The system supports both synchronous
and asynchronous event handling with filtering and error handling.
"""

from .core import Event, EventHandler, EventManager, emit_event, get_event_manager
from .decorators import async_event_handler, event_handler
from .filters import CompositeFilter, EventFilter, SourceFilter, TypeFilter
from .types import EventData, EventPriority, EventType

__all__ = [
    "EventManager",
    "Event",
    "EventHandler",
    "EventType",
    "EventPriority",
    "EventData",
    "event_handler",
    "async_event_handler",
    "EventFilter",
    "TypeFilter",
    "SourceFilter",
    "CompositeFilter",
    "emit_event",
    "get_event_manager",
]
