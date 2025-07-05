"""Export manager for converting server configurations to various formats.

This module provides the ExportManager class which handles the conversion of
parsed server configurations to different client formats (sing-box, Clash,
v2ray, etc.). It manages format-specific exporters, routing rule generation,
version compatibility checks, and Phase 3 postprocessor/middleware integration.

Phase 4 enhancements:
- PostProcessorChain integration for server filtering and enhancement
- MiddlewareChain support for data enrichment and logging
- Profile-based configuration of processing chains
- Backward compatibility with existing export workflows
"""

from typing import List, Dict, Any, Optional, Union
from sboxmgr.subscription.models import ParsedServer, ClientProfile, PipelineContext
from sboxmgr.profiles.models import FullProfile
from sboxmgr.logging import get_logger
from .routing.default_router import DefaultRouter
from sboxmgr.subscription.exporters.singbox_exporter import singbox_export
from sboxmgr.subscription.exporters.clashexporter import clash_export

# Import Phase 3 components
try:
    from sboxmgr.subscription.postprocessors import PostProcessorChain
    from sboxmgr.subscription.middleware import BaseMiddleware
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False
    PostProcessorChain = None
    BaseMiddleware = None

# Lazy logger initialization to avoid import-time dependency issues
def _get_logger():
    """Get logger instance with lazy initialization."""
    return get_logger(__name__)

EXPORTER_REGISTRY = {
    "singbox": singbox_export,
    "clash": clash_export,
    # В будущем: "v2ray": v2ray_export и т.д.
}

class ExportManager:
    """Manages configuration export for various proxy clients with Phase 3 integration.
    
    This class handles the export of parsed server configurations to different
    client formats (sing-box, Clash, v2ray, etc.) with routing rules generation,
    client profile customization, version compatibility checks, and Phase 3
    postprocessor/middleware chain processing.
    
    Phase 4 enhancements:
    - Integrated PostProcessorChain for server filtering and enhancement
    - MiddlewareChain support for data enrichment and logging
    - Profile-based configuration of processing chains
    - Maintains full backward compatibility
    
    Attributes:
        routing_plugin: Plugin for generating routing rules.
        export_format: Target export format (singbox, clash, v2ray, etc.).
        client_profile: Client configuration profile for inbound generation.
        postprocessor_chain: Optional PostProcessorChain for server processing.
        middleware_chain: Optional MiddlewareChain for data enrichment.
        profile: Optional FullProfile for profile-based configuration.

    """
    
    def __init__(self, 
                 routing_plugin=None, 
                 export_format="singbox", 
                 client_profile: Optional[ClientProfile] = None,
                 postprocessor_chain: Optional['PostProcessorChain'] = None,
                 middleware_chain: Optional[List['BaseMiddleware']] = None,
                 profile: Optional[FullProfile] = None):
        """Initialize export manager with configuration and Phase 3 components.

        Args:
            routing_plugin: Optional routing plugin for rule generation. 
                          Defaults to DefaultRouter if not provided.
            export_format: Target export format. Defaults to "singbox".
            client_profile: Optional client profile for inbound configuration.
            postprocessor_chain: Optional PostProcessorChain for server processing.
            middleware_chain: Optional list of middleware components.
            profile: Optional FullProfile for profile-based configuration.

        """
        self.routing_plugin = routing_plugin or DefaultRouter()
        self.export_format = export_format
        self.client_profile = client_profile
        self.postprocessor_chain = postprocessor_chain
        self.middleware_chain = middleware_chain or []
        self.profile = profile
        
        # Auto-configure middleware from client_profile if available and no manual middleware
        if client_profile and PHASE3_AVAILABLE and not middleware_chain:
            self._auto_configure_middleware_from_client_profile(client_profile)

    def export(self, 
               servers: List[ParsedServer], 
               exclusions: Optional[List[str]] = None, 
               user_routes: Optional[List[Dict]] = None, 
               context: Union[Dict[str, Any], PipelineContext] = None, 
               client_profile: Optional[ClientProfile] = None, 
               profile: Optional[FullProfile] = None) -> Dict:
        """Export servers to configuration format with optional Phase 3 processing.
        
        Args:
            servers: List of server configurations to export.
            exclusions: List of server identifiers to exclude.
            user_routes: Optional user-defined routing rules.
            context: Pipeline context or dictionary with context data.
            client_profile: Optional client configuration profile.
            profile: Optional profile for processing.
            
        Returns:
            Dictionary containing exported configuration.

        """
        # Convert context to PipelineContext if needed
        if isinstance(context, dict):
            context = PipelineContext(**context)
        elif context is None:
            context = PipelineContext(mode="direct_export")
        
        # Apply exclusions
        filtered_servers = servers
        if exclusions:
            filtered_servers = [s for s in servers if not any(ex in str(s) for ex in exclusions)]
        
        # Get routing rules
        routes = user_routes or []
        if self.routing_plugin:
            try:
                routes = self.routing_plugin.generate_routes(
                    filtered_servers, 
                    exclusions or [], 
                    user_routes or [],
                    context
                )
            except Exception as e:
                _get_logger().warning(f"Routing plugin failed: {e}")
                routes = []
        
        # Apply Phase 3 processing if available
        processed_servers = filtered_servers
        active_profile = profile or self.profile
        
        if PHASE3_AVAILABLE:
            # Apply middleware
            if self.middleware_chain:
                for middleware in self.middleware_chain:
                    try:
                        processed_servers = middleware.process(
                            processed_servers, 
                            context, 
                            active_profile
                        )
                    except Exception as e:
                        _get_logger().warning(f"Middleware {middleware.__class__.__name__} failed: {e}")
            
            # Apply postprocessor chain
            if self.postprocessor_chain:
                try:
                    processed_servers = self.postprocessor_chain.process(
                        processed_servers, 
                        context, 
                        active_profile
                    )
                except Exception as e:
                    _get_logger().warning(f"PostProcessor chain failed: {e}")
        
        # Export with format-specific handling
        exporter_func = EXPORTER_REGISTRY.get(self.export_format)
        if not exporter_func:
            _get_logger().warning(f"Unknown export format: {self.export_format}, falling back to singbox")
            exporter_func = EXPORTER_REGISTRY.get("singbox", singbox_export)
        
        if self.export_format == "singbox":
            # Use middleware-aware export if middleware is configured
            if self.middleware_chain and PHASE3_AVAILABLE:
                try:
                    from sboxmgr.subscription.exporters.singbox_exporter import singbox_export_with_middleware
                    return singbox_export_with_middleware(
                        processed_servers, 
                        routes, 
                        client_profile=client_profile or self.client_profile,
                        context=context
                    )
                except ImportError:
                    _get_logger().warning("Middleware-aware export not available, falling back to standard export")
            
            return exporter_func(
                processed_servers, 
                routes, 
                client_profile=client_profile or self.client_profile
            )
        else:
            return exporter_func(processed_servers, routes)
    
    def export_to_singbox(self, 
                         servers: List[ParsedServer], 
                         routes: Optional[List[Dict]] = None, 
                         client_profile: Optional[ClientProfile] = None, 
                         apply_phase3_processing: bool = True,
                         context: Optional[PipelineContext] = None,
                         profile: Optional[FullProfile] = None) -> Dict:
        """Simplified method for exporting to sing-box format with Phase 3 support.
        
        Provides a direct interface for sing-box export with optional Phase 3
        postprocessor and middleware processing. Useful for cases where routing
        rules are already prepared or not needed.
        
        Args:
            servers: List of server configurations to export.
            routes: Optional pre-prepared routing rules.
            client_profile: Optional client configuration profile.
            apply_phase3_processing: Whether to apply Phase 3 processing.
            context: Optional pipeline context.
            profile: Optional profile for processing.
            
        Returns:
            Dictionary containing sing-box configuration.

        """
        routes = routes or []
        client_profile = client_profile or self.client_profile
        active_profile = profile or self.profile
        
        # Apply Phase 3 processing if requested and available
        processed_servers = servers
        if apply_phase3_processing and PHASE3_AVAILABLE:
            pipeline_context = context or PipelineContext(mode="direct_export")
            
            # Apply middleware
            if self.middleware_chain:
                for middleware in self.middleware_chain:
                    try:
                        processed_servers = middleware.process(
                            processed_servers, 
                            pipeline_context, 
                            active_profile
                        )
                    except Exception as e:
                        _get_logger().warning(f"Middleware {middleware.__class__.__name__} failed: {e}")
            
            # Apply postprocessor chain
            if self.postprocessor_chain:
                try:
                    processed_servers = self.postprocessor_chain.process(
                        processed_servers, 
                        pipeline_context, 
                        active_profile
                    )
                except Exception as e:
                    _get_logger().warning(f"PostProcessor chain failed: {e}")
        
        exporter_func = EXPORTER_REGISTRY.get("singbox", singbox_export)
        return exporter_func(
            processed_servers, 
            routes, 
            client_profile=client_profile
        )
    
    def configure_from_profile(self, profile: FullProfile) -> 'ExportManager':
        """Configure ExportManager from FullProfile with Phase 3 components.
        
        Creates and configures PostProcessorChain and MiddlewareChain based on
        profile configuration. Returns a new ExportManager instance with the
        configured components.
        
        Args:
            profile: FullProfile containing processing configuration.
            
        Returns:
            New ExportManager instance configured from profile.

        """
        if not PHASE3_AVAILABLE:
            # Return current instance if Phase 3 not available
            return ExportManager(
                routing_plugin=self.routing_plugin,
                export_format=self.export_format,
                client_profile=self.client_profile,
                profile=profile
            )
        
        # Configure PostProcessorChain from profile
        postprocessor_chain = None
        if hasattr(profile, 'filter') and profile.filter:
            # Extract postprocessor configuration from profile
            postprocessor_config = self._extract_postprocessor_config(profile)
            if postprocessor_config:
                postprocessor_chain = self._create_postprocessor_chain(postprocessor_config)
        
        # Configure MiddlewareChain from profile
        middleware_chain = []
        if hasattr(profile, 'metadata') and profile.metadata:
            middleware_config = profile.metadata.get('middleware', {})
            if middleware_config:
                middleware_chain = self._create_middleware_chain(middleware_config)
        
        return ExportManager(
            routing_plugin=self.routing_plugin,
            export_format=self.export_format,
            client_profile=self.client_profile,
            postprocessor_chain=postprocessor_chain,
            middleware_chain=middleware_chain,
            profile=profile
        )
    
    def _extract_postprocessor_config(self, profile: FullProfile) -> Optional[Dict[str, Any]]:
        """Extract postprocessor configuration from profile.
        
        Args:
            profile: FullProfile to extract configuration from.
            
        Returns:
            Dictionary with postprocessor configuration or None.

        """
        if not hasattr(profile, 'filter') or not profile.filter:
            return None
        
        # Extract configuration from FilterProfile
        config = {}
        filter_profile = profile.filter
        
        # Geo filter configuration
        if hasattr(filter_profile, 'allowed_countries') and filter_profile.allowed_countries:
            config['geo_filter'] = {
                'allowed_countries': filter_profile.allowed_countries,
                'blocked_countries': getattr(filter_profile, 'blocked_countries', [])
            }
        
        # Tag filter configuration  
        if hasattr(filter_profile, 'include_tags') and filter_profile.include_tags:
            config['tag_filter'] = {
                'include_tags': filter_profile.include_tags,
                'exclude_tags': getattr(filter_profile, 'exclude_tags', [])
            }
        
        return config if config else None
    
    def _create_postprocessor_chain(self, config: Dict[str, Any]) -> Optional['PostProcessorChain']:
        """Create PostProcessorChain from configuration.
        
        Args:
            config: Configuration dictionary for postprocessors.
            
        Returns:
            Configured PostProcessorChain or None.

        """
        if not PHASE3_AVAILABLE:
            return None
        
        from sboxmgr.subscription.postprocessors import (
            GeoFilterPostProcessor,
            TagFilterPostProcessor,
            LatencySortPostProcessor
        )
        
        processors = []
        
        # Add geo filter if configured
        if 'geo_filter' in config:
            processors.append(GeoFilterPostProcessor(config['geo_filter']))
        
        # Add tag filter if configured
        if 'tag_filter' in config:
            processors.append(TagFilterPostProcessor(config['tag_filter']))
        
        # Add latency sort if configured
        if 'latency_sort' in config:
            processors.append(LatencySortPostProcessor(config['latency_sort']))
        
        if processors:
            return PostProcessorChain(processors, {
                'execution_mode': 'sequential',
                'error_strategy': 'continue'
            })
        
        return None
    
    def _create_middleware_chain(self, config: Dict[str, Any]) -> List['BaseMiddleware']:
        """Create middleware chain from configuration.
        
        Args:
            config: Configuration dictionary for middleware.
            
        Returns:
            List of configured middleware components.

        """
        if not PHASE3_AVAILABLE:
            return []
        
        middleware_chain = []
        
        # Add logging middleware if enabled
        if config.get('logging', {}).get('enabled', False):
            try:
                from sboxmgr.subscription.middleware import LoggingMiddleware
                middleware_chain.append(LoggingMiddleware(config.get('logging', {})))
            except ImportError:
                pass
        
        # Add enrichment middleware if enabled
        if config.get('enrichment', {}).get('enabled', False):
            try:
                from sboxmgr.subscription.middleware import EnrichmentMiddleware
                middleware_chain.append(EnrichmentMiddleware(config.get('enrichment', {})))
            except ImportError:
                pass
        
        return middleware_chain
    
    @property
    def has_phase3_components(self) -> bool:
        """Check if Phase 3 components are available and configured.
        
        Returns:
            True if Phase 3 components are available and configured.

        """
        return (PHASE3_AVAILABLE and 
                (self.postprocessor_chain is not None or 
                 len(self.middleware_chain) > 0))
    
    def get_processing_metadata(self) -> Dict[str, Any]:
        """Get metadata about configured processing components.
        
        Returns:
            Dictionary with metadata about processing configuration.

        """
        metadata = {
            'export_format': self.export_format,
            'has_routing_plugin': self.routing_plugin is not None,
            'has_client_profile': self.client_profile is not None,
            'phase3_available': PHASE3_AVAILABLE,
            'has_postprocessor_chain': self.postprocessor_chain is not None,
            'middleware_count': len(self.middleware_chain),
            'has_profile': self.profile is not None
        }
        
        if self.postprocessor_chain:
            metadata['postprocessor_chain'] = self.postprocessor_chain.get_metadata()
        
        if self.middleware_chain:
            metadata['middleware_types'] = [m.__class__.__name__ for m in self.middleware_chain]
        
        return metadata
    
    def _auto_configure_middleware_from_client_profile(self, client_profile: ClientProfile) -> None:
        """Auto-configure middleware based on client profile settings.
        
        Automatically adds OutboundFilterMiddleware and RouteConfigMiddleware
        if the client profile has exclude_outbounds or routing configuration.
        
        Args:
            client_profile: Client profile with configuration

        """
        if not PHASE3_AVAILABLE:
            return
        
        try:
            from sboxmgr.subscription.middleware import OutboundFilterMiddleware, RouteConfigMiddleware
            
            # Add outbound filter middleware if exclude_outbounds is configured
            if client_profile.exclude_outbounds:
                outbound_filter = OutboundFilterMiddleware({
                    'exclude_types': client_profile.exclude_outbounds,
                    'strict_mode': False,
                    'preserve_metadata': True
                })
                self.middleware_chain.append(outbound_filter)
            
            # Add route config middleware if routing is configured
            if client_profile.routing:
                route_config = RouteConfigMiddleware({
                    'final_action': client_profile.routing.get('final', 'auto'),
                    'override_mode': 'profile_overrides',
                    'preserve_metadata': True
                })
                self.middleware_chain.append(route_config)
                
        except ImportError:
            _get_logger().warning("Phase 3 middleware not available for auto-configuration")
        except Exception as e:
            _get_logger().warning(f"Failed to auto-configure middleware: {e}") 