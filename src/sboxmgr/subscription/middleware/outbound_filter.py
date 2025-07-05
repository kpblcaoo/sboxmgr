"""Outbound filtering middleware implementation.

This module provides middleware functionality for filtering outbound types
based on ClientProfile configuration. It supports excluding specific outbound
types from the final configuration.

Implements Phase 3 architecture with profile integration.
"""

from typing import List, Optional, Dict, Any
from ..registry import register
from .base import ProfileAwareMiddleware
from ..models import ParsedServer, PipelineContext, ClientProfile
from ...profiles.models import FullProfile


@register("outbound_filter")
class OutboundFilterMiddleware(ProfileAwareMiddleware):
    """Outbound filtering middleware with profile integration.
    
    Filters servers based on outbound type exclusions defined in ClientProfile.
    This middleware removes servers of excluded outbound types before they
    reach the exporter, providing early filtering in the pipeline.
    
    Configuration options:
    - exclude_types: List of outbound types to exclude
    - strict_mode: Whether to fail if no servers remain after filtering
    - preserve_metadata: Whether to preserve filtering metadata in context
    
    Example:
        middleware = OutboundFilterMiddleware({
            'exclude_types': ['vmess', 'shadowsocks'],
            'strict_mode': False
        })
        filtered_servers = middleware.process(servers, context, profile)

    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize outbound filter with configuration.
        
        Args:
            config: Configuration dictionary with filtering options

        """
        super().__init__(config)
        self.exclude_types = set(self.config.get('exclude_types', []))
        self.strict_mode = self.config.get('strict_mode', False)
        self.preserve_metadata = self.config.get('preserve_metadata', True)
    
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Filter servers based on outbound type exclusions.
        
        Args:
            servers: List of servers to filter
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of servers with excluded outbound types removed

        """
        if not servers:
            return servers
        
        # Extract exclude configuration from profile
        exclude_config = self._extract_exclude_config(profile)
        
        if not exclude_config['exclude_types']:
            return servers
        
        # Apply outbound type filtering
        original_count = len(servers)
        filtered_servers = []
        excluded_servers = []
        
        for server in servers:
            if server.type in exclude_config['exclude_types']:
                excluded_servers.append(server)
            else:
                filtered_servers.append(server)
        
        # Handle strict mode
        if self.strict_mode and not filtered_servers:
            raise ValueError(
                f"All servers were excluded by outbound filter. "
                f"Excluded types: {exclude_config['exclude_types']}"
            )
        
        # Preserve metadata in context
        if self.preserve_metadata and context:
            if 'outbound_filter' not in context.metadata:
                context.metadata['outbound_filter'] = {}
            
            context.metadata['outbound_filter'].update({
                'excluded_types': list(exclude_config['exclude_types']),
                'excluded_count': len(excluded_servers),
                'original_count': original_count,
                'filtered_count': len(filtered_servers),
                'excluded_servers': [
                    {'type': s.type, 'tag': s.tag, 'address': s.address}
                    for s in excluded_servers
                ]
            })
        
        return filtered_servers
    
    def _extract_exclude_config(self, profile: Optional[FullProfile]) -> Dict[str, Any]:
        """Extract exclude configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            Dictionary with exclude configuration

        """
        exclude_config = {
            'exclude_types': self.exclude_types.copy()
        }
        
        if not profile:
            return exclude_config
        
        # Check for client profile in context or profile
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
                        f"Using default exclude configuration."
                    )
                    client_profile = None
        
        # If we have a client profile, merge exclude configuration
        if client_profile and client_profile.exclude_outbounds:
            exclude_config['exclude_types'].update(client_profile.exclude_outbounds)
        
        return exclude_config
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None, profile: Optional[FullProfile] = None) -> bool:
        """Check if outbound filtering can be applied.
        
        Args:
            servers: List of servers
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            bool: True if outbound filtering is applicable

        """
        if not servers:
            return False
        
        # Use merged exclude_types from config and profile
        exclude_config = self._extract_exclude_config(profile)
        if not exclude_config['exclude_types']:
            return False
        
        # Check if any servers have the excluded types
        server_types = {server.type for server in servers}
        return bool(server_types & exclude_config['exclude_types'])
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get middleware metadata.
        
        Returns:
            Dictionary with middleware metadata

        """
        return {
            'type': 'outbound_filter',
            'exclude_types': list(self.exclude_types),
            'strict_mode': self.strict_mode,
            'preserve_metadata': self.preserve_metadata
        } 