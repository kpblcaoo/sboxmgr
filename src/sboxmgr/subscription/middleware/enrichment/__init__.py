"""Enrichment middleware package.

This package provides modular data enrichment functionality for subscription
processing, refactored from the original monolithic enrichment.py file.
"""

from .basic import BasicEnricher
from .core import EnrichmentMiddleware
from .custom import CustomEnricher
from .geo import GeoEnricher
from .performance import PerformanceEnricher
from .security import SecurityEnricher

# Main export
__all__ = [
    # Main middleware class
    "EnrichmentMiddleware",
    # Individual enrichers
    "BasicEnricher",
    "GeoEnricher",
    "PerformanceEnricher",
    "SecurityEnricher",
    "CustomEnricher",
]
