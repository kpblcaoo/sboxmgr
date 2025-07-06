"""Structured logging system with multi-sink support and trace ID propagation.

Implements ADR-0010 Logging Core Architecture providing:
- Automatic sink detection (journald → syslog → stdout)
- Structured logging with trace ID propagation
- Multiple output formats (JSON, human-readable, compact)
- Service mode vs CLI mode auto-adjustment
"""

from .core import (
    LoggingCore,
    StructuredLoggerAdapter,
    get_logger,
    initialize_logging,
    reconfigure_logging,
)
from .formatters import create_formatter, get_default_formatter
from .sinks import LogSink, detect_available_sinks
from .trace import (
    clear_trace_id,
    copy_trace_context,
    generate_trace_id,
    get_trace_id,
    set_trace_id,
    with_trace_id,
)

__all__ = [
    # Core logging system
    "LoggingCore",
    "StructuredLoggerAdapter",
    "initialize_logging",
    "get_logger",
    "reconfigure_logging",
    # Trace ID system
    "get_trace_id",
    "set_trace_id",
    "with_trace_id",
    "generate_trace_id",
    "clear_trace_id",
    "copy_trace_context",
    # Sinks and formatters
    "LogSink",
    "detect_available_sinks",
    "create_formatter",
    "get_default_formatter",
]
