"""Event system for sboxmgr.

This module provides a comprehensive event system for configuration updates,
service notifications, and plugin hooks. The system supports both synchronous
and asynchronous event handling with filtering and error handling.
"""

from .core import EventManager, Event, EventHandler, emit_event, get_event_manager
from .types import EventType, EventPriority, EventData
from .decorators import event_handler, async_event_handler
from .filters import EventFilter, TypeFilter, SourceFilter, CompositeFilter

__all__ = [
    'EventManager',
    'Event', 
    'EventHandler',
    'EventType',
    'EventPriority',
    'EventData',
    'event_handler',
    'async_event_handler',
    'EventFilter',
    'TypeFilter',
    'SourceFilter',
    'CompositeFilter',
    'emit_event',
    'get_event_manager',
] 