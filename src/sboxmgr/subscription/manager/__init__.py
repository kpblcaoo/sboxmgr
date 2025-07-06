"""Subscription manager package.

This package provides modular subscription management functionality,
refactored from the original monolithic manager.py file.
"""

from .core import SubscriptionManager
from .parser_detector import detect_parser
from .cache import CacheManager
from .error_handler import ErrorHandler
from .data_processor import DataProcessor
from .pipeline_coordinator import PipelineCoordinator

# Main exports
__all__ = [
    # Main manager class
    "SubscriptionManager",
    
    # Individual components
    "detect_parser",
    "CacheManager",
    "ErrorHandler",
    "DataProcessor",
    "PipelineCoordinator",
]
