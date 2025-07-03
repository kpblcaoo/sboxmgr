"""Subscription post-processors package for Phase 3 architecture.

Post-processors run after parsing and optional middleware pipelines to clean
up, deduplicate, filter, sort, or enrich the list of `ParsedServer` objects before export.
Each post-processor implements the enhanced `BasePostProcessor` interface with
profile integration and advanced features.

Phase 3 enhancements:
- Profile-aware processing
- Enhanced error handling
- Metadata collection
- Chain execution strategies
- Conditional processing
"""

# Import legacy postprocessors for backward compatibility
from .geofilterpostprocessor import *
from .geofilterpostprocessorpostprocessor import *

# Import new Phase 3 postprocessors
from .base import BasePostProcessor, ProfileAwarePostProcessor, ChainablePostProcessor
from .geo_filter import GeoFilterPostProcessor
from .tag_filter import TagFilterPostProcessor
from .latency_sort import LatencySortPostProcessor
from .chain import PostProcessorChain

__all__ = [
    # Base classes
    'BasePostProcessor',
    'ProfileAwarePostProcessor', 
    'ChainablePostProcessor',
    
    # Concrete postprocessors
    'GeoFilterPostProcessor',
    'TagFilterPostProcessor',
    'LatencySortPostProcessor',
    'PostProcessorChain',
    
    # Legacy postprocessors (for backward compatibility)
    'GeoFilterPostProcessorPostprocessor',
] 