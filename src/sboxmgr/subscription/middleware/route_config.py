"""Route configuration middleware implementation.

This module provides middleware functionality for configuring routing
parameters based on ClientProfile configuration. It supports setting
final route actions and other routing parameters.

Implements Phase 3 architecture with profile integration.
"""

from typing import List, Optional, Dict, Any
from ..registry import register
from .base import ProfileAwareMiddleware
from ..models import ParsedServer, PipelineContext, ClientProfile
from ...profiles.models import FullProfile


@register("route_config")
class RouteConfigMiddleware(ProfileAwareMiddleware):
    """Route configuration middleware with profile integration.
    
    Configures routing parameters based on ClientProfile configuration.
    This middleware sets final route actions and other routing parameters
    in the pipeline context for use by exporters.
    
    Configuration options:
    - final_action: Default final route action
    - preserve_metadata: Whether to preserve routing metadata in context
    - override_mode: How to handle conflicts ('profile_overrides', 'config_overrides')
    
    Example:
        middleware = RouteConfigMiddleware({
            'final_action': 'proxy-out',
            'override_mode': 'profile_overrides'
        })
        processed_servers = middleware.process(servers, context, profile)

    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize route config with configuration.
        
        Args:
            config: Configuration dictionary with routing options

        """
        super().__init__(config)
        self.final_action = self.config.get('final_action', 'auto')
        self.preserve_metadata = self.config.get('preserve_metadata', True)
        self.override_mode = self.config.get('override_mode', 'profile_overrides')
    
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Configure routing parameters based on profile.
        
        Args:
            servers: List of servers to process
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of servers (unchanged, but context is updated)

        """
        if not context:
            return servers
        
        # Extract routing configuration from profile
        route_config = self._extract_route_config(profile)
        
        # Set routing parameters in context
        if 'routing' not in context.metadata:
            context.metadata['routing'] = {}
        
        context.metadata['routing'].update({
            'final_action': route_config['final_action'],
            'configured_by': 'route_config_middleware',
            'override_mode': self.override_mode
        })
        
        # Preserve detailed metadata if requested
        if self.preserve_metadata:
            context.metadata['routing'].update({
                'config_source': route_config['config_source'],
                'original_final_action': route_config['original_final_action'],
                'profile_has_routing': route_config['profile_has_routing']
            })
        
        return servers
    
    def _extract_route_config(self, profile: Optional[FullProfile]) -> Dict[str, Any]:
        """Extract routing configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            Dictionary with routing configuration

        """
        route_config = {
            'final_action': self.final_action,
            'config_source': 'middleware_config',
            'original_final_action': self.final_action,
            'profile_has_routing': False
        }
        
        if not profile:
            return route_config
        
        # Check for client profile in profile metadata
        client_profile = None
        
        # Try to get from profile metadata
        if hasattr(profile, 'metadata') and 'client_profile' in profile.metadata:
            client_profile_data = profile.metadata['client_profile']
            if isinstance(client_profile_data, dict):
                try:
                    client_profile = ClientProfile(**client_profile_data)
                except Exception as e:
                    # Log error but continue processing with default config
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Failed to create ClientProfile from metadata: {e}. "
                        f"Using default routing configuration."
                    )
                    client_profile = None
        
        # If we have a client profile with routing configuration
        if client_profile and client_profile.routing:
            route_config['profile_has_routing'] = True
            
            # Handle override mode
            if self.override_mode == 'profile_overrides':
                # Profile routing overrides middleware config
                profile_final = client_profile.routing.get('final')
                if profile_final:
                    route_config['final_action'] = profile_final
                    route_config['config_source'] = 'client_profile'
            elif self.override_mode == 'config_overrides':
                # Middleware config overrides profile (keep current)
                pass
            else:  # 'merge' mode - use profile if available, otherwise config
                profile_final = client_profile.routing.get('final')
                if profile_final:
                    route_config['final_action'] = profile_final
                    route_config['config_source'] = 'client_profile'
        
        return route_config
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None) -> bool:
        """Check if route configuration can be applied.
        
        Args:
            servers: List of servers
            context: Pipeline context
            
        Returns:
            bool: True if route configuration is applicable

        """
        # This middleware can always process (it just configures context)
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get middleware metadata.
        
        Returns:
            Dictionary with middleware metadata

        """
        return {
            'type': 'route_config',
            'final_action': self.final_action,
            'override_mode': self.override_mode,
            'preserve_metadata': self.preserve_metadata
        } 