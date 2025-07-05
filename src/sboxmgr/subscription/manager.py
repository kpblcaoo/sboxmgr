"""Subscription management and orchestration - Compatibility Layer.

This module provides backward compatibility for the refactored subscription
manager. The original monolithic implementation has been modularized
into separate components for better maintainability.

Original implementation: manager_legacy.py
New modular implementation: manager/
"""

# Import from new modular implementation
from .manager import SubscriptionManager, detect_parser

# Legacy compatibility - export main components
__all__ = ['SubscriptionManager', 'detect_parser']

# Note: This compatibility layer ensures that existing code continues to work
# without any changes. The actual implementation is now in the manager/
# package with separate modules for different responsibilities. 