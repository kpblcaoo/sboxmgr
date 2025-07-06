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

# Import new Phase 3 postprocessors
from .base import BasePostProcessor, ChainablePostProcessor, ProfileAwarePostProcessor
from .chain import PostProcessorChain
from .geo_filter import GeoFilterPostProcessor
from .latency_sort import LatencySortPostProcessor
from .tag_filter import TagFilterPostProcessor

__all__ = [
    # Base classes
    "BasePostProcessor",
    "ProfileAwarePostProcessor",
    "ChainablePostProcessor",
    # Concrete postprocessors
    "GeoFilterPostProcessor",
    "TagFilterPostProcessor",
    "LatencySortPostProcessor",
    "PostProcessorChain",
]
