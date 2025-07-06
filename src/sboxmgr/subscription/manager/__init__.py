"""Subscription manager package.

This package provides modular subscription management functionality,
refactored from the original monolithic manager.py file.
"""

from .cache import CacheManager
from .core import SubscriptionManager
from .data_processor import DataProcessor
from .error_handler import ErrorHandler
from .parser_detector import detect_parser
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
