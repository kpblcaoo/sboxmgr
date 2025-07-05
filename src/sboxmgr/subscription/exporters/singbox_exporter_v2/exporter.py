"""Main exporter class for sing-box exporter v2.

This module provides the SingboxExporterV2 class that implements the BaseExporter
interface using the modular Pydantic models for better validation and type safety.
"""

import logging
from typing import List, Optional
from ...models import ParsedServer, ClientProfile
from ...base_exporter import BaseExporter
from ...registry import register

# Import new sing-box models
from sboxmgr.models.singbox import (
    SingBoxConfig, LogConfig, DirectOutbound, BlockOutbound,
    RouteConfig, RouteRule
)

from .converter import convert_parsed_server_to_outbound
from .inbound_converter import convert_client_profile_to_inbounds

logger = logging.getLogger(__name__)


@register("singbox_v2")
class SingboxExporterV2(BaseExporter):
    """New Sing-box configuration exporter using modular Pydantic models.
    
    This exporter provides better validation, type safety, and maintainability
    compared to the legacy exporter. It uses the modular Pydantic models
    from sboxmgr.models.singbox for full validation.
    """
    
    def export(self, servers: List[ParsedServer], client_profile: Optional[ClientProfile] = None) -> str:
        """Export servers to sing-box JSON configuration string.
        
        Args:
            servers: List of ParsedServer objects to export
            client_profile: Optional ClientProfile for inbound configuration
            
        Returns:
            JSON string containing sing-box configuration
            
        Raises:
            ValueError: If server data is invalid or cannot be exported
        """
        try:
            # Convert servers to outbounds
            outbounds = []
            for server in servers:
                outbound = convert_parsed_server_to_outbound(server)
                if outbound:
                    outbounds.append(outbound)
            
            # Add default outbounds
            outbounds.extend([
                DirectOutbound(type="direct", tag="direct"),
                BlockOutbound(type="block", tag="block")
            ])
            
            # Convert client profile to inbounds
            inbounds = []
            if client_profile:
                inbounds = convert_client_profile_to_inbounds(client_profile)
            
            # Create basic routing rules
            routing_rules = [
                RouteRule(outbound="direct", network="tcp"),
                RouteRule(outbound="direct", network="udp")
            ]
            
            # Create sing-box configuration
            config_data = {
                "log": LogConfig(level="info"),
                "inbounds": inbounds,
                "outbounds": outbounds,
                "route": RouteConfig(
                    rules=routing_rules,
                    final="direct"
                )
            }
            
            # Validate and export
            config = SingBoxConfig(**config_data)
            return config.to_json(indent=2)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise ValueError(f"Failed to export configuration: {e}") 