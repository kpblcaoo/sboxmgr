"""Subscription middleware package for Phase 3 architecture.

Middleware components process subscription data between pipeline stages,
providing transformation, filtering, enrichment, logging, and other
cross-cutting concerns. Each middleware implements the enhanced
`BaseMiddleware` interface with profile integration.

Phase 3 enhancements:
- Profile-aware processing
- Enhanced context support
- Metadata collection
- Error handling strategies
- Conditional execution
- Chain coordination
"""

from .base import (
    BaseMiddleware,
    ProfileAwareMiddleware,
    ChainableMiddleware,
    ConditionalMiddleware,
    TransformMiddleware
)
from .logging import LoggingMiddleware
from .enrichment import EnrichmentMiddleware

__all__ = [
    # Base classes
    'BaseMiddleware',
    'ProfileAwareMiddleware',
    'ChainableMiddleware',
    'ConditionalMiddleware',
    'TransformMiddleware',
    
    # Concrete middleware
    'LoggingMiddleware',
    'EnrichmentMiddleware',
] 