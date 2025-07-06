"""Data enrichment middleware implementation - Compatibility Layer.

This module provides backward compatibility for the refactored enrichment
middleware. The original monolithic implementation has been modularized
into separate components for better maintainability.

Original implementation: enrichment_legacy.py
New modular implementation: enrichment/
"""

# Import from new modular implementation
from .enrichment import EnrichmentMiddleware

# Legacy compatibility - export the main class
__all__ = ['EnrichmentMiddleware']

# Note: This compatibility layer ensures that existing code continues to work
# without any changes. The actual implementation is now in the enrichment/
# package with separate modules for different types of enrichment.
