"""Chain builders for postprocessors and middleware."""

from typing import List, Optional, Any

import typer

from sboxmgr.i18n.t import t
from .validators import validate_postprocessors, validate_middleware

# Import Phase 3 components
try:
    from sboxmgr.subscription.postprocessors import (
        PostProcessorChain,
        GeoFilterPostProcessor,
        TagFilterPostProcessor,
        LatencySortPostProcessor
    )
    from sboxmgr.subscription.middleware import LoggingMiddleware, EnrichmentMiddleware
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    PostProcessorChain = None
    GeoFilterPostProcessor = None
    TagFilterPostProcessor = None
    LatencySortPostProcessor = None
    LoggingMiddleware = None
    EnrichmentMiddleware = None


def create_postprocessor_chain_from_list(processors: List[str]) -> Optional['PostProcessorChain']:
    """Create PostProcessorChain from list of processor names.
    
    Args:
        processors: List of processor names (geo_filter, tag_filter, latency_sort)
        
    Returns:
        Configured PostProcessorChain or None
        
    Raises:
        typer.Exit: If invalid processor names found
    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  PostProcessor chains require Phase 3 components", err=True)
        return None
    
    # Validate processor names
    validate_postprocessors(processors)
    
    processor_instances = []
    processor_map = {
        'geo_filter': GeoFilterPostProcessor,
        'tag_filter': TagFilterPostProcessor,
        'latency_sort': LatencySortPostProcessor
    }
    
    for proc_name in processors:
        # Use default configuration for CLI-specified processors
        processor_instances.append(processor_map[proc_name]({}))
        typer.echo(f"✅ {t('cli.success.postprocessor_added').format(name=proc_name)}")
    
    if processor_instances:
        return PostProcessorChain(processor_instances, {
            'execution_mode': 'sequential',
            'error_strategy': 'continue'
        })
    
    return None


def create_middleware_chain_from_list(middleware: List[str]) -> List[Any]:
    """Create middleware chain from list of middleware names.
    
    Args:
        middleware: List of middleware names (logging, enrichment)
        
    Returns:
        List of configured middleware instances
        
    Raises:
        typer.Exit: If invalid middleware names found
    """
    if not PHASE3_AVAILABLE:
        typer.echo("⚠️  Middleware chains require Phase 3 components", err=True)
        return []
    
    # Validate middleware names
    validate_middleware(middleware)
    
    middleware_instances = []
    middleware_map = {
        'logging': LoggingMiddleware,
        'enrichment': EnrichmentMiddleware
    }
    
    for mw_name in middleware:
        # Use default configuration for CLI-specified middleware
        middleware_instances.append(middleware_map[mw_name]({}))
        typer.echo(f"✅ {t('cli.success.middleware_added').format(name=mw_name)}")
    
    return middleware_instances
