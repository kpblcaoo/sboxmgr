"""Enrichment middleware package.

This package provides modular data enrichment functionality for subscription
processing, refactored from the original monolithic enrichment.py file.
"""

from .core import EnrichmentMiddleware
from .basic import BasicEnricher
from .geo import GeoEnricher
from .performance import PerformanceEnricher
from .security import SecurityEnricher
from .custom import CustomEnricher

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