"""Subscription-related exception classes and error handling.

This module defines custom exception classes for subscription processing
errors including fetch failures, parse errors, validation failures, and
export errors. These exceptions provide structured error information for
better error handling and debugging throughout the subscription pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, Any

class ErrorType(Enum):
    """Enumeration of pipeline error types.
    
    Defines the different categories of errors that can occur during
    the subscription processing pipeline.
    """
    
    VALIDATION = "validation"
    FETCH = "fetch"
    PARSE = "parse"
    PLUGIN = "plugin"
    INTERNAL = "internal"

@dataclass
class PipelineError:
    """Represents an error that occurred during pipeline execution.
    
    This class encapsulates error information including type, stage,
    message, context, and timestamp for debugging and error reporting.
    
    Attributes:
        type: The category of error that occurred.
        stage: The pipeline stage where the error occurred.
        message: Human-readable error description.
        context: Additional context information about the error.
        timestamp: When the error occurred (UTC).
    """
    
    type: ErrorType
    stage: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)