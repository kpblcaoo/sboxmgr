"""Performance enrichment functionality for server data."""

import time
from typing import Any

from ...models import ParsedServer, PipelineContext


class PerformanceEnricher:
    """Provides performance-related metadata enrichment for servers.

    Adds performance indicators like latency estimation, protocol efficiency,
    security level, and reliability scores based on server characteristics.
    """

    def __init__(self, cache_duration: int = 300):
        """Initialize performance enricher.

        Args:
            cache_duration: How long to cache performance data in seconds

        """
        self.cache_duration = cache_duration
        self._cache: dict[str, tuple[dict[str, Any], float]] = {}

    def enrich(self, server: ParsedServer, context: PipelineContext) -> ParsedServer:
        """Apply performance enrichment to a server.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with performance enrichment applied

        """
        server_key = f"{server.address}:{server.port}"

        # Check cache first
        if server_key in self._cache:
            cached_data, timestamp = self._cache[server_key]
            if time.time() - timestamp < self.cache_duration:
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
            self._cache[server_key] = (performance_info, time.time())

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
            country = geo_info.get("country", "").upper()

            # Low latency regions
            if country in ["US", "CA", "GB", "DE", "FR", "JP", "KR", "SG", "NL", "CH"]:
                return "low"
            # Medium latency regions
            elif country in ["CN", "RU", "IN", "BR", "AU", "ZA", "TR", "MX"]:
                return "medium"
            # High latency regions (remote or with poor connectivity)
            elif country:
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
            # High efficiency protocols
            "wireguard": "high",
            "vless": "high",
            "hysteria2": "high",
            "tuic": "high",
            # Medium efficiency protocols
            "vmess": "medium",
            "trojan": "medium",
            "shadowsocks": "medium",
            "ss": "medium",
            "shadowtls": "medium",
            # Low efficiency protocols
            "http": "low",
            "socks": "low",
            "socks5": "low",
        }

        return efficiency_map.get(protocol_type.lower(), "medium")

    def _get_security_level(self, server: ParsedServer) -> str:
        """Get security level for server.

        Args:
            server: Server to analyze

        Returns:
            Security level ('high', 'medium', 'low')

        """
        # Base security by protocol
        protocol_security = {
            # High security protocols
            "wireguard": "high",
            "vless": "high",
            "vmess": "high",
            "trojan": "high",
            "hysteria2": "high",
            "tuic": "high",
            "shadowtls": "high",
            # Medium security protocols
            "shadowsocks": "medium",
            "ss": "medium",
            # Low security protocols
            "http": "low",
            "socks": "low",
            "socks5": "low",
        }

        base_security = protocol_security.get(server.type.lower(), "medium")

        # Adjust based on encryption/security settings
        if hasattr(server, "security") and server.security:
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
        # Base reliability by protocol
        protocol_reliability = {
            "wireguard": 0.9,
            "vless": 0.8,
            "trojan": 0.8,
            "hysteria2": 0.85,
            "tuic": 0.8,
            "vmess": 0.7,
            "shadowsocks": 0.7,
            "ss": 0.7,
            "shadowtls": 0.75,
            "http": 0.5,
            "socks": 0.5,
            "socks5": 0.5,
        }

        score = protocol_reliability.get(server.type.lower(), 0.6)

        # Adjust based on port (standard ports are more reliable)
        standard_ports = {443, 80, 8080, 8443, 1080, 1194, 51820}
        if server.port in standard_ports:
            score += 0.05

        # Adjust based on security
        if hasattr(server, "security") and server.security:
            if server.security in ["tls", "reality", "xtls"]:
                score += 0.1
            elif server.security == "none":
                score -= 0.1

        # Adjust based on geographic location
        if "geo" in server.meta:
            geo_info = server.meta["geo"]
            country = geo_info.get("country", "").upper()

            # Reliable regions
            if country in ["US", "CA", "GB", "DE", "FR", "JP", "NL", "CH", "SG"]:
                score += 0.05
            # Less reliable regions
            elif country in ["CN", "RU", "IR", "PK"]:
                score -= 0.05

        return min(1.0, max(0.0, score))
