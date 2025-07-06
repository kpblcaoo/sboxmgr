"""Data enrichment middleware implementation for Phase 3 architecture.

This module provides middleware for enriching server data with additional
metadata, geographic information, performance metrics, and other useful
information that can be used by postprocessors and exporters.

Implements Phase 3 architecture with profile integration.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional

from ...profiles.models import FullProfile
from ..models import ParsedServer, PipelineContext
from .base import TransformMiddleware


class EnrichmentMiddleware(TransformMiddleware):
    """Data enrichment middleware with profile integration.

    Enriches server data with additional metadata including geographic
    information, performance metrics, security indicators, and custom
    attributes based on profile configuration.

    Configuration options:
    - enable_geo_enrichment: Add geographic metadata
    - enable_performance_enrichment: Add performance indicators
    - enable_security_enrichment: Add security metadata
    - enable_custom_enrichment: Add custom attributes from profile
    - geo_database_path: Path to geographic database
    - performance_cache_duration: How long to cache performance data
    - custom_enrichers: List of custom enrichment functions
    - max_enrichment_time: Maximum time to spend on enrichment per server

    Example:
        middleware = EnrichmentMiddleware({
            'enable_geo_enrichment': True,
            'enable_performance_enrichment': True,
            'geo_database_path': '/path/to/geoip.db'
        })
        enriched_servers = middleware.process(servers, context, profile)

    """

    middleware_type = "enrichment"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enrichment middleware.

        Args:
            config: Configuration dictionary for enrichment options

        """
        super().__init__(config)
        self.enable_geo_enrichment = self.config.get("enable_geo_enrichment", True)
        self.enable_performance_enrichment = self.config.get(
            "enable_performance_enrichment", True
        )
        self.enable_security_enrichment = self.config.get(
            "enable_security_enrichment", True
        )
        self.enable_custom_enrichment = self.config.get(
            "enable_custom_enrichment", True
        )
        self.geo_database_path = self.config.get("geo_database_path")
        self.performance_cache_duration = self.config.get(
            "performance_cache_duration", 300
        )
        self.custom_enrichers = self.config.get("custom_enrichers", [])
        self.max_enrichment_time = self.config.get("max_enrichment_time", 1.0)

        # Initialize caches
        self._geo_cache: Dict[str, Dict[str, Any]] = {}
        self._performance_cache: Dict[str, Dict[str, Any]] = {}
        self._security_cache: Dict[str, Dict[str, Any]] = {}

    def _do_process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> List[ParsedServer]:
        """Enrich servers with additional metadata.

        Args:
            servers: List of servers to enrich
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            List of enriched servers

        """
        if not servers:
            return servers

        # Extract enrichment configuration from profile
        enrichment_config = self._extract_enrichment_config(profile)

        enriched_servers = []
        for server in servers:
            start_time = time.time()

            try:
                # Apply basic enrichment
                enriched_server = self._enrich_server(
                    server, context, profile, enrichment_config
                )
                enriched_servers.append(enriched_server)

                # Check time limit
                if time.time() - start_time > self.max_enrichment_time:
                    # If enrichment is taking too long, add remaining servers without enrichment
                    enriched_servers.extend(servers[len(enriched_servers) :])
                    break

            except Exception as e:
                # On error, add server with error metadata
                server.meta["enrichment_error"] = str(e)
                enriched_servers.append(server)

        return enriched_servers

    def _extract_enrichment_config(
        self, profile: Optional[FullProfile]
    ) -> Dict[str, Any]:
        """Extract enrichment configuration from profile.

        Args:
            profile: Full profile configuration

        Returns:
            Dictionary with enrichment configuration

        """
        enrichment_config = {
            "enable_geo_enrichment": self.enable_geo_enrichment,
            "enable_performance_enrichment": self.enable_performance_enrichment,
            "enable_security_enrichment": self.enable_security_enrichment,
            "enable_custom_enrichment": self.enable_custom_enrichment,
            "custom_enrichers": self.custom_enrichers.copy(),
        }

        if not profile:
            return enrichment_config

        # Check for enrichment-specific metadata in profile
        if "enrichment" in profile.metadata:
            enrichment_meta = profile.metadata["enrichment"]
            for key in enrichment_config:
                if key in enrichment_meta:
                    enrichment_config[key] = enrichment_meta[key]

        return enrichment_config

    def _enrich_server(
        self,
        server: ParsedServer,
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
        enrichment_config: Optional[Dict[str, Any]] = None,
    ) -> ParsedServer:
        """Enrich a single server with metadata.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
            enrichment_config: Enrichment configuration

        Returns:
            Enriched server

        """
        if not enrichment_config:
            enrichment_config = self._extract_enrichment_config(profile)

        # Apply basic metadata enrichment
        server = self._apply_basic_enrichment(server, context)

        # Apply geographic enrichment
        if enrichment_config["enable_geo_enrichment"]:
            server = self._apply_geo_enrichment(server, context)

        # Apply performance enrichment
        if enrichment_config["enable_performance_enrichment"]:
            server = self._apply_performance_enrichment(server, context)

        # Apply security enrichment
        if enrichment_config["enable_security_enrichment"]:
            server = self._apply_security_enrichment(server, context)

        # Apply custom enrichment
        if enrichment_config["enable_custom_enrichment"]:
            server = self._apply_custom_enrichment(
                server, context, profile, enrichment_config
            )

        return server

    def _apply_basic_enrichment(
        self, server: ParsedServer, context: PipelineContext
    ) -> ParsedServer:
        """Apply basic metadata enrichment.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with basic enrichment

        """
        # Add processing metadata
        server.meta["enriched_at"] = time.time()
        server.meta["trace_id"] = context.trace_id

        # Add server identifier hash
        server_id = f"{server.type}://{server.address}:{server.port}"
        server.meta["server_id"] = hashlib.sha256(server_id.encode()).hexdigest()[:8]

        # Add source information
        if context.source:
            server.meta["source"] = context.source

        # Normalize server tag
        if not server.tag and "name" in server.meta:
            server.tag = server.meta["name"]
        elif not server.tag:
            server.tag = f"{server.type}-{server.address}"

        return server

    def _apply_geo_enrichment(
        self, server: ParsedServer, context: PipelineContext
    ) -> ParsedServer:
        """Apply geographic enrichment.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with geographic enrichment

        """
        server_key = server.address

        # Check cache first
        if server_key in self._geo_cache:
            server.meta["geo"] = self._geo_cache[server_key]
            return server

        geo_info = {}

        try:
            # Try to get geographic information
            geo_info = self._lookup_geographic_info(server.address)

            # Cache the result
            self._geo_cache[server_key] = geo_info

        except Exception as e:
            geo_info["error"] = str(e)

        if geo_info:
            server.meta["geo"] = geo_info

        return server

    def _lookup_geographic_info(self, address: str) -> Dict[str, Any]:
        """Look up geographic information for an address.

        Args:
            address: Server address to look up

        Returns:
            Dictionary with geographic information

        """
        geo_info = {}

        # Skip private/local addresses
        if self._is_private_address(address):
            geo_info["type"] = "private"
            return geo_info

        try:
            # Try using geoip2 if available and database path is provided
            if self.geo_database_path:
                import geoip2.database
                import geoip2.errors

                with geoip2.database.Reader(self.geo_database_path) as reader:
                    response = reader.city(address)
                    geo_info.update(
                        {
                            "country": response.country.iso_code,
                            "country_name": response.country.name,
                            "city": response.city.name,
                            "latitude": (
                                float(response.location.latitude)
                                if response.location.latitude
                                else None
                            ),
                            "longitude": (
                                float(response.location.longitude)
                                if response.location.longitude
                                else None
                            ),
                            "timezone": response.location.time_zone,
                        }
                    )
            else:
                # Fallback: try to extract country from domain TLD
                if "." in address and not address.replace(".", "").isdigit():
                    tld = address.split(".")[-1].upper()
                    if len(tld) == 2:
                        geo_info["country"] = tld
                        geo_info["source"] = "tld"

        except Exception:
            # If all methods fail, mark as unknown
            geo_info["country"] = "unknown"
            geo_info["source"] = "unknown"

        return geo_info

    def _is_private_address(self, address: str) -> bool:
        """Check if address is private/local.

        Args:
            address: Address to check

        Returns:
            bool: True if address is private

        """
        import ipaddress

        try:
            ip = ipaddress.ip_address(address)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # Not an IP address, assume it's a domain
            return address in ["localhost", "127.0.0.1", "::1"] or address.startswith(
                "192.168."
            )

    def _apply_performance_enrichment(
        self, server: ParsedServer, context: PipelineContext
    ) -> ParsedServer:
        """Apply performance-related enrichment.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with performance enrichment

        """
        server_key = f"{server.address}:{server.port}"

        # Check cache first
        if server_key in self._performance_cache:
            cached_data, timestamp = self._performance_cache[server_key]
            if time.time() - timestamp < self.performance_cache_duration:
                server.meta["performance"] = cached_data
                return server

        performance_info = {}

        try:
            # Add performance indicators
            performance_info.update(
                {
                    "estimated_latency_class": self._estimate_latency_class(server),
                    "protocol_efficiency": self._get_protocol_efficiency(server.type),
                    "security_level": self._get_security_level(server),
                    "reliability_score": self._calculate_reliability_score(server),
                }
            )

            # Cache the result
            self._performance_cache[server_key] = (performance_info, time.time())

        except Exception as e:
            performance_info["error"] = str(e)

        if performance_info:
            server.meta["performance"] = performance_info

        return server

    def _estimate_latency_class(self, server: ParsedServer) -> str:
        """Estimate latency class based on server characteristics.

        Args:
            server: Server to analyze

        Returns:
            Latency class ('low', 'medium', 'high', 'unknown')

        """
        # Basic heuristics for latency estimation
        if "geo" in server.meta:
            geo_info = server.meta["geo"]
            if geo_info.get("country") in [
                "US",
                "CA",
                "GB",
                "DE",
                "FR",
                "JP",
                "KR",
                "SG",
            ]:
                return "low"
            elif geo_info.get("country") in ["CN", "RU", "IN", "BR", "AU"]:
                return "medium"
            else:
                return "high"

        return "unknown"

    def _get_protocol_efficiency(self, protocol_type: str) -> str:
        """Get efficiency rating for protocol type.

        Args:
            protocol_type: Protocol type

        Returns:
            Efficiency rating ('high', 'medium', 'low')

        """
        efficiency_map = {
            "wireguard": "high",
            "vless": "high",
            "vmess": "medium",
            "trojan": "medium",
            "shadowsocks": "medium",
            "ss": "medium",
            "http": "low",
            "socks": "low",
        }

        return efficiency_map.get(protocol_type.lower(), "medium")

    def _get_security_level(self, server: ParsedServer) -> str:
        """Get security level for server.

        Args:
            server: Server to analyze

        Returns:
            Security level ('high', 'medium', 'low')

        """
        protocol_security = {
            "wireguard": "high",
            "vless": "high",
            "vmess": "high",
            "trojan": "high",
            "shadowsocks": "medium",
            "ss": "medium",
            "http": "low",
            "socks": "low",
        }

        base_security = protocol_security.get(server.type.lower(), "medium")

        # Adjust based on encryption/security settings
        if server.security in ["tls", "reality", "xtls"]:
            return "high"
        elif server.security in ["none", "auto"]:
            return "low" if base_security == "high" else "medium"

        return base_security

    def _calculate_reliability_score(self, server: ParsedServer) -> float:
        """Calculate reliability score for server.

        Args:
            server: Server to analyze

        Returns:
            Reliability score (0.0 to 1.0)

        """
        score = 0.5  # Base score

        # Adjust based on protocol
        protocol_reliability = {
            "wireguard": 0.9,
            "vless": 0.8,
            "vmess": 0.7,
            "trojan": 0.8,
            "shadowsocks": 0.7,
            "ss": 0.7,
            "http": 0.5,
            "socks": 0.5,
        }

        score = protocol_reliability.get(server.type.lower(), 0.6)

        # Adjust based on port (standard ports are more reliable)
        standard_ports = {443, 80, 8080, 8443, 1080, 1194}
        if server.port in standard_ports:
            score += 0.1

        # Adjust based on security
        if server.security in ["tls", "reality", "xtls"]:
            score += 0.1

        return min(1.0, score)

    def _apply_security_enrichment(
        self, server: ParsedServer, context: PipelineContext
    ) -> ParsedServer:
        """Apply security-related enrichment.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with security enrichment

        """
        security_info = {}

        try:
            security_info.update(
                {
                    "encryption_level": self._get_encryption_level(server),
                    "port_classification": self._classify_port(server.port),
                    "protocol_vulnerabilities": self._get_protocol_vulnerabilities(
                        server.type
                    ),
                    "recommended_settings": self._get_recommended_settings(server),
                }
            )

        except Exception as e:
            security_info["error"] = str(e)

        if security_info:
            server.meta["security"] = security_info

        return server

    def _get_encryption_level(self, server: ParsedServer) -> str:
        """Get encryption level for server.

        Args:
            server: Server to analyze

        Returns:
            Encryption level ('strong', 'moderate', 'weak', 'none')

        """
        if server.security in ["tls", "reality", "xtls"]:
            return "strong"
        elif server.security in ["auto", "aes-256-gcm", "chacha20-poly1305"]:
            return "moderate"
        elif server.security in ["none"]:
            return "none"
        else:
            return "weak"

    def _classify_port(self, port: int) -> str:
        """Classify port type.

        Args:
            port: Port number

        Returns:
            Port classification

        """
        if port in [80, 8080]:
            return "http"
        elif port in [443, 8443]:
            return "https"
        elif port == 1080:
            return "socks"
        elif port == 1194:
            return "openvpn"
        elif 1024 <= port <= 65535:
            return "high"
        else:
            return "system"

    def _get_protocol_vulnerabilities(self, protocol_type: str) -> List[str]:
        """Get known vulnerabilities for protocol.

        Args:
            protocol_type: Protocol type

        Returns:
            List of vulnerability descriptions

        """
        vulnerabilities = {
            "vmess": ["timing_attack_v1", "weak_uuid_generation"],
            "shadowsocks": ["replay_attack", "traffic_analysis"],
            "http": ["no_encryption", "plain_text"],
            "socks": ["no_authentication", "plain_text"],
        }

        return vulnerabilities.get(protocol_type.lower(), [])

    def _get_recommended_settings(self, server: ParsedServer) -> Dict[str, Any]:
        """Get recommended security settings for server.

        Args:
            server: Server to analyze

        Returns:
            Dictionary with recommended settings

        """
        recommendations = {}

        if server.type.lower() == "vmess":
            recommendations.update(
                {"alterId": 0, "security": "auto", "network": "ws", "tls": True}
            )
        elif server.type.lower() in ["shadowsocks", "ss"]:
            recommendations.update(
                {
                    "method": "aes-256-gcm",
                    "plugin": "v2ray-plugin",
                    "plugin_opts": {"mode": "websocket", "tls": True},
                }
            )

        return recommendations

    def _apply_custom_enrichment(
        self,
        server: ParsedServer,
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
        enrichment_config: Optional[Dict[str, Any]] = None,
    ) -> ParsedServer:
        """Apply custom enrichment based on profile configuration.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
            enrichment_config: Enrichment configuration

        Returns:
            Server with custom enrichment

        """
        if not profile or not enrichment_config:
            return server

        # Apply custom enrichers from configuration
        for enricher_name in enrichment_config.get("custom_enrichers", []):
            try:
                if enricher_name == "subscription_tags":
                    self._apply_subscription_tags(server, context, profile)
                elif enricher_name == "priority_scoring":
                    self._apply_priority_scoring(server, context, profile)
                elif enricher_name == "compatibility_check":
                    self._apply_compatibility_check(server, context, profile)

            except Exception as e:
                server.meta[f"custom_enrichment_error_{enricher_name}"] = str(e)

        return server

    def _apply_subscription_tags(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Apply subscription-based tags.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration

        """
        # Find matching subscription
        for sub_profile in profile.subscriptions:
            if context.source and sub_profile.id in context.source:
                server.meta["subscription_id"] = sub_profile.id
                server.meta["subscription_priority"] = sub_profile.priority
                server.meta["subscription_enabled"] = sub_profile.enabled
                break

    def _apply_priority_scoring(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Apply priority scoring based on profile preferences.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration

        """
        priority_score = 0.5  # Base score

        # Adjust based on filter preferences
        if profile.filters.only_tags and server.tag:
            if server.tag in profile.filters.only_tags:
                priority_score += 0.3

        # Adjust based on routing preferences
        if hasattr(profile.routing, "preferred_countries"):
            server_country = server.meta.get("geo", {}).get("country")
            if server_country in profile.routing.preferred_countries:
                priority_score += 0.2

        server.meta["priority_score"] = min(1.0, priority_score)

    def _apply_compatibility_check(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Check compatibility with export format.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration

        """
        compatibility = {"compatible": True, "issues": []}

        export_format = profile.export.format

        if export_format == "sing-box":
            # Check sing-box compatibility
            if server.type not in [
                "shadowsocks",
                "vmess",
                "vless",
                "trojan",
                "wireguard",
            ]:
                compatibility["compatible"] = False
                compatibility["issues"].append(
                    f"Protocol {server.type} not supported by sing-box"
                )

        elif export_format == "clash":
            # Check clash compatibility
            if server.type not in ["shadowsocks", "vmess", "trojan", "http", "socks"]:
                compatibility["compatible"] = False
                compatibility["issues"].append(
                    f"Protocol {server.type} not supported by clash"
                )

        server.meta["compatibility"] = compatibility
