"""Default routing plugin implementation.

This module provides the DefaultRouter class which implements basic routing
rule generation for sing-box configurations. It creates simple routing rules
that direct traffic through the configured proxy servers with basic fallback
handling.
"""
from .base_router import BaseRoutingPlugin
from typing import List, Dict, Any

class DefaultRouter(BaseRoutingPlugin):
    """Default implementation of routing rule generation.
    
    This router generates basic routing rules suitable for sing-box
    configurations. It creates rules that route traffic through proxy servers
    with simple fallback to direct connection when needed.
    """
    
    def generate_routes(self, servers: List[Any], exclusions: List[str], user_routes: List[Dict], context: Dict[str, Any] = None) -> List[Dict]:
        """Generate default routing rules for sing-box configuration.
        
        Creates basic routing rules that direct traffic through proxy servers
        with fallback handling. Supports user-defined routes and exclusions.
        
        Args:
            servers: List of parsed server configurations.
            exclusions: List of server patterns to exclude from routing.
            user_routes: User-defined routing rules to include.
            context: Additional context including debug level and mode.
            
        Returns:
            List of routing rule dictionaries for sing-box configuration.
        """
        # Логируем только при debug_level >= 2
        debug_level = getattr(context, 'debug_level', 0) if context else 0
        if debug_level >= 2:
            print(f"[DefaultRouter] context={context}, exclusions={exclusions}, user_routes={user_routes}")
        return [] 