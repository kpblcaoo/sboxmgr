"""Trace ID propagation system using ContextVar.

Implements EVENT-02 from ADR-0011: ContextVar + auto-generation for trace-ID propagation.
Provides automatic trace ID flow through call stack without manual parameter passing.
"""

import uuid
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional, Generator


# Context variable for trace ID propagation
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')


def get_trace_id() -> str:
    """Get current trace ID or generate new one.
    
    Automatically generates a new trace ID if none exists in current context.
    Uses short 8-character UUID for readability in logs.
    
    Returns:
        str: Current trace ID (8 characters)
        
    Example:
        >>> trace_id = get_trace_id()
        >>> len(trace_id)
        8

    """
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set trace ID for current context.
    
    Manually sets trace ID for current execution context.
    Useful for external requests or when inheriting trace ID from upstream.
    
    Args:
        trace_id: Trace ID to set (will be truncated to 8 characters)
        
    Example:
        >>> set_trace_id("abc12345")
        >>> get_trace_id()
        'abc12345'

    """
    # Ensure trace ID is max 8 characters for consistency
    normalized_trace_id = str(trace_id)[:8]
    trace_id_var.set(normalized_trace_id)


@contextmanager
def with_trace_id(trace_id: Optional[str] = None) -> Generator[str, None, None]:
    """Context manager for trace ID scoping.
    
    Creates isolated trace ID scope that automatically resets when exiting.
    Generates new trace ID if none provided.
    
    Args:
        trace_id: Optional trace ID to use. If None, generates new one.
        
    Yields:
        str: The trace ID being used in this scope
        
    Example:
        >>> with with_trace_id("test1234") as tid:
        ...     print(f"Using trace ID: {tid}")
        ...     print(f"Retrieved: {get_trace_id()}")
        Using trace ID: test1234
        Retrieved: test1234

    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]
    else:
        trace_id = str(trace_id)[:8]
    
    token = trace_id_var.set(trace_id)
    try:
        yield trace_id
    finally:
        trace_id_var.reset(token)


def generate_trace_id() -> str:
    """Generate new trace ID without setting it.
    
    Creates a new 8-character trace ID based on UUID4.
    Does not modify current context.
    
    Returns:
        str: New trace ID (8 characters)
        
    Example:
        >>> tid = generate_trace_id()
        >>> len(tid)
        8

    """
    return str(uuid.uuid4())[:8]


def clear_trace_id() -> None:
    """Clear trace ID from current context.
    
    Removes trace ID from current context. Next call to get_trace_id()
    will generate a new one.
    
    Example:
        >>> set_trace_id("test1234")
        >>> get_trace_id()
        'test1234'
        >>> clear_trace_id()
        >>> # Next get_trace_id() will generate new ID

    """
    trace_id_var.set('')


def copy_trace_context() -> str:
    """Copy current trace ID for passing to other contexts.
    
    Useful for manual trace ID propagation to external systems
    or when crossing context boundaries.
    
    Returns:
        str: Current trace ID, or new one if none exists
        
    Example:
        >>> current_trace = copy_trace_context()
        >>> # Pass to external system or different context

    """
    return get_trace_id() 