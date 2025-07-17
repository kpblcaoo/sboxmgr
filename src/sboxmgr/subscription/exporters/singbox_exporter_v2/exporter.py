"""Main exporter class for sing-box exporter v2.

This module provides the SingboxExporterV2 class that implements the BaseExporter
interface using the modular Pydantic models for better validation and type safety.
"""

import logging
from typing import Optional

# Import new sing-box models
from sboxmgr.models.singbox import (
    BlockOutbound,
    DirectOutbound,
    LogConfig,
    RouteConfig,
    RouteRule,
    UrlTestOutbound,
)

from ...base_exporter import BaseExporter
from ...models import ClientProfile, ParsedServer
from ...registry import register
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

    def export(
        self,
        servers: list[ParsedServer],
        client_profile: Optional[ClientProfile] = None,
    ) -> str:
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
            proxy_tags = []

            for server in servers:
                outbound = convert_parsed_server_to_outbound(server)
                if outbound:
                    outbounds.append(outbound)
                    proxy_tags.append(outbound.tag)

            # Add URLTest outbound if there are proxy servers (like legacy)
            if proxy_tags:
                urltest_outbound = UrlTestOutbound(
                    type="urltest",
                    tag="auto",
                    outbounds=proxy_tags,
                    url="https://www.gstatic.com/generate_204",
                    interval="3m",
                    tolerance=50,
                    idle_timeout="30m",  # 30 minutes as string
                    interrupt_exist_connections=False,
                )
                outbounds.insert(0, urltest_outbound)

            # Add default outbounds
            outbounds.extend(
                [
                    DirectOutbound(type="direct", tag="direct"),
                    BlockOutbound(type="block", tag="block"),
                ]
            )

            # Convert client profile to inbounds
            inbounds = []
            if client_profile:
                inbounds = convert_client_profile_to_inbounds(client_profile)

            # Create smart routing rules
            routing_rules = []

            # Private IP ranges - direct (using correct field name)
            routing_rules.append(
                RouteRule(
                    source_ip_cidr=[
                        "10.0.0.0/8",
                        "172.16.0.0/12",
                        "192.168.0.0/16",
                        "127.0.0.0/8",
                    ],
                    outbound="direct",
                )
            )

            # Default rule for all other traffic to auto
            if proxy_tags:
                routing_rules.append(RouteRule(network="tcp", outbound="auto"))
                routing_rules.append(RouteRule(network="udp", outbound="auto"))

            # Determine final action
            final_action = "auto" if proxy_tags else "direct"

            # Create sing-box configuration
            config_data = {
                "log": LogConfig(level="info").model_dump(exclude_none=True),
                "inbounds": [inbound.smart_dump() for inbound in inbounds],
                "outbounds": [outbound.smart_dump() for outbound in outbounds],
                "route": RouteConfig(
                    rules=[
                        rule.model_dump(exclude_none=True) for rule in routing_rules
                    ],
                    final=final_action,
                ).model_dump(exclude_none=True),
            }

            # Remove empty sections
            config_data = {k: v for k, v in config_data.items() if v}

            # Export as JSON
            import json

            return json.dumps(config_data, indent=2)

        except Exception as e:
            logger.error(f"Failed to export config: {e}")
            raise ValueError(f"Config export failed: {e}") from e
