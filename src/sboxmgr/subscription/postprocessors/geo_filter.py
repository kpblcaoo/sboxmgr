"""Geographic filtering postprocessor implementation.

This module provides postprocessing functionality for filtering servers
based on geographic location. It supports country-based filtering, region
filtering, and custom geographic rules for optimizing server selection
based on user location and preferences.

Implements Phase 3 architecture with profile integration.
"""

from typing import List, Optional, Dict, Any
from ..registry import register
from .base import ProfileAwarePostProcessor
from ..models import ParsedServer, PipelineContext
from ...profiles.models import FullProfile


@register("geo_filter")
class GeoFilterPostProcessor(ProfileAwarePostProcessor):
    """Geographic filtering postprocessor with profile integration.
    
    Filters servers based on geographic criteria defined in profiles
    or configuration. Supports country codes, region filtering, and
    custom geographic rules.
    
    Configuration options:
    - allowed_countries: List of allowed country codes (ISO 3166-1 alpha-2)
    - blocked_countries: List of blocked country codes
    - preferred_regions: List of preferred regions (priority ordering)
    - max_distance_km: Maximum distance from user location (if available)
    - fallback_mode: What to do if no servers match criteria ('allow_all', 'block_all')
    
    Example:
        processor = GeoFilterPostProcessor({
            'allowed_countries': ['US', 'CA', 'GB'],
            'blocked_countries': ['CN', 'RU'],
            'fallback_mode': 'allow_all'
        })
        filtered_servers = processor.process(servers, context, profile)

    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize geo filter with configuration.
        
        Args:
            config: Configuration dictionary with filtering options

        """
        super().__init__(config)
        self.allowed_countries = self.config.get('allowed_countries', [])
        self.blocked_countries = self.config.get('blocked_countries', [])
        self.preferred_regions = self.config.get('preferred_regions', [])
        self.max_distance_km = self.config.get('max_distance_km')
        self.fallback_mode = self.config.get('fallback_mode', 'allow_all')
    
    def process(
        self, 
        servers: List[ParsedServer], 
        context: Optional[PipelineContext] = None,
        profile: Optional[FullProfile] = None
    ) -> List[ParsedServer]:
        """Filter servers based on geographic criteria.
        
        Args:
            servers: List of servers to filter
            context: Pipeline context
            profile: Full profile configuration
            
        Returns:
            List of servers that match geographic criteria

        """
        if not servers:
            return servers
        
        # Extract geographic configuration from profile if available
        geo_config = self._extract_geo_config(profile)
        
        # Apply geographic filtering
        filtered_servers = []
        for server in servers:
            if self._should_include_server(server, geo_config, context):
                filtered_servers.append(server)
        
        # Apply fallback logic if no servers match
        if not filtered_servers and self.fallback_mode == 'allow_all':
            return servers
        
        return filtered_servers
    
    def _extract_geo_config(self, profile: Optional[FullProfile]) -> Dict[str, Any]:
        """Extract geographic configuration from profile.
        
        Args:
            profile: Full profile configuration
            
        Returns:
            Dictionary with geographic configuration

        """
        geo_config = {
            'allowed_countries': self.allowed_countries,
            'blocked_countries': self.blocked_countries,
            'preferred_regions': self.preferred_regions,
            'max_distance_km': self.max_distance_km
        }
        
        if not profile:
            return geo_config
        
        # Check if profile has geographic metadata
        if 'geo' in profile.metadata:
            profile_geo = profile.metadata['geo']
            if 'allowed_countries' in profile_geo:
                geo_config['allowed_countries'] = profile_geo['allowed_countries']
            if 'blocked_countries' in profile_geo:
                geo_config['blocked_countries'] = profile_geo['blocked_countries']
            if 'preferred_regions' in profile_geo:
                geo_config['preferred_regions'] = profile_geo['preferred_regions']
        
        return geo_config
    
    def _should_include_server(
        self, 
        server: ParsedServer, 
        geo_config: Dict[str, Any],
        context: Optional[PipelineContext] = None
    ) -> bool:
        """Check if server should be included based on geographic criteria.
        
        Args:
            server: Server to check
            geo_config: Geographic configuration
            context: Pipeline context
            
        Returns:
            bool: True if server should be included

        """
        # Extract country code from server metadata
        country_code = self._extract_country_code(server)
        
        if not country_code:
            # If no country information, apply fallback logic
            return self.fallback_mode == 'allow_all'
        
        # Check blocked countries first
        if country_code in geo_config['blocked_countries']:
            return False
        
        # Check allowed countries
        if geo_config['allowed_countries']:
            return country_code in geo_config['allowed_countries']
        
        # If no specific allowed countries, allow all except blocked
        return True
    
    def _extract_country_code(self, server: ParsedServer) -> Optional[str]:
        """Extract country code from server metadata.
        
        Args:
            server: Server to extract country from
            
        Returns:
            ISO 3166-1 alpha-2 country code or None

        """
        # Check various metadata fields for country information
        if 'country' in server.meta:
            return server.meta['country'].upper()
        
        if 'geo' in server.meta:
            geo_info = server.meta['geo']
            if isinstance(geo_info, dict) and 'country' in geo_info:
                return geo_info['country'].upper()
        
        # Try to extract from tag (e.g., "US-Server-1" -> "US")
        if server.tag:
            parts = server.tag.split('-')
            if len(parts) > 0 and len(parts[0]) == 2:
                return parts[0].upper()
        
        # Try to extract from address (basic heuristic)
        if '.' in server.address and not server.address.replace('.', '').isdigit():
            # Domain name - try to extract TLD as country hint
            tld = server.address.split('.')[-1].upper()
            if len(tld) == 2:
                return tld
        
        return None
    
    def can_process(self, servers: List[ParsedServer], context: Optional[PipelineContext] = None) -> bool:
        """Check if geo filtering can be applied.
        
        Args:
            servers: List of servers
            context: Pipeline context
            
        Returns:
            bool: True if geo filtering is applicable

        """
        if not servers:
            return False
        
        # Check if any servers have geographic metadata
        for server in servers:
            if self._extract_country_code(server):
                return True
        
        # Can still process even without geo data (fallback mode)
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this postprocessor.
        
        Returns:
            Dict containing postprocessor metadata

        """
        metadata = super().get_metadata()
        metadata.update({
            'allowed_countries': self.allowed_countries,
            'blocked_countries': self.blocked_countries,
            'preferred_regions': self.preferred_regions,
            'max_distance_km': self.max_distance_km,
            'fallback_mode': self.fallback_mode
        })
        return metadata 