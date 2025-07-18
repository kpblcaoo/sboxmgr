"""Custom enrichment functionality for server data."""

from typing import Any, Optional

from ....configs.models import FullProfile
from ...models import ParsedServer, PipelineContext


class CustomEnricher:
    """Provides custom enrichment based on profile configuration.

    Applies profile-specific enrichment including subscription tags,
    priority scoring, and compatibility checks based on export format.
    """

    def __init__(self, custom_enrichers: Optional[list[str]] = None):
        """Initialize custom enricher.

        Args:
            custom_enrichers: List of custom enricher names to apply
        """
        self.custom_enrichers = custom_enrichers or []

    def enrich(
        self,
        server: ParsedServer,
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
        enrichers: Optional[list[str]] = None,
    ) -> ParsedServer:
        """Apply custom enrichment to a server.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
            enrichers: List of enrichers to apply (overrides instance config)

        Returns:
            Server with custom enrichment applied
        """
        if not profile:
            return server

        enrichers_to_apply = enrichers or self.custom_enrichers

        # Apply custom enrichers from configuration
        for enricher_name in enrichers_to_apply:
            try:
                if enricher_name == "subscription_tags":
                    self._apply_subscription_tags(server, context, profile)
                elif enricher_name == "priority_scoring":
                    self._apply_priority_scoring(server, context, profile)
                elif enricher_name == "compatibility_check":
                    self._apply_compatibility_check(server, context, profile)
                elif enricher_name == "region_preference":
                    self._apply_region_preference(server, context, profile)
                elif enricher_name == "usage_hints":
                    self._apply_usage_hints(server, context, profile)

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
        if hasattr(profile, "subscriptions") and profile.subscriptions:
            for sub_profile in profile.subscriptions:
                if context.source and sub_profile.id in context.source:
                    server.meta["subscription_id"] = sub_profile.id
                    server.meta["subscription_priority"] = getattr(
                        sub_profile, "priority", 1
                    )
                    server.meta["subscription_enabled"] = getattr(
                        sub_profile, "enabled", True
                    )
                    if hasattr(sub_profile, "tags"):
                        server.meta["subscription_tags"] = sub_profile.tags
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
        if hasattr(profile, "filters") and profile.filters:
            # Preferred tags
            if (
                hasattr(profile.filters, "only_tags")
                and profile.filters.only_tags
                and server.tag
            ):
                if server.tag in profile.filters.only_tags:
                    priority_score += 0.3

            # Excluded tags (negative scoring)
            if (
                hasattr(profile.filters, "exclude_tags")
                and profile.filters.exclude_tags
                and server.tag
            ):
                if server.tag in profile.filters.exclude_tags:
                    priority_score -= 0.4

        # Adjust based on routing preferences
        if hasattr(profile, "routing") and profile.routing:
            # Preferred countries
            if (
                hasattr(profile.routing, "preferred_countries")
                and profile.routing.preferred_countries
            ):
                server_country = server.meta.get("geo", {}).get("country")
                if (
                    server_country
                    and server_country in profile.routing.preferred_countries
                ):
                    priority_score += 0.2

        # Adjust based on performance data
        if "performance" in server.meta:
            perf_data = server.meta["performance"]

            # Latency preference
            latency_class = perf_data.get("estimated_latency_class", "unknown")
            if latency_class == "low":
                priority_score += 0.15
            elif latency_class == "high":
                priority_score -= 0.1

            # Security level preference
            security_level = perf_data.get("security_level", "medium")
            if security_level == "high":
                priority_score += 0.1
            elif security_level == "low":
                priority_score -= 0.15

        server.meta["priority_score"] = max(0.0, min(1.0, priority_score))

    def _apply_compatibility_check(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Check compatibility with export format.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
        """
        compatibility: dict[str, Any] = {"compatible": True, "issues": []}

        if not hasattr(profile, "export") or not profile.export:
            server.meta["compatibility"] = compatibility
            return

        export_format = profile.export.format

        if export_format == "sing-box":
            # Check sing-box compatibility
            supported_protocols = {
                "shadowsocks",
                "vmess",
                "vless",
                "trojan",
                "wireguard",
                "hysteria2",
                "tuic",
                "shadowtls",
                "ssh",
                "tor",
            }
            if server.type not in supported_protocols:
                compatibility["compatible"] = False
                compatibility["issues"].append(
                    f"Protocol {server.type} not supported by sing-box"
                )

        elif export_format == "clash":
            # Check clash compatibility
            supported_protocols = {
                "shadowsocks",
                "vmess",
                "trojan",
                "http",
                "socks",
                "socks5",
            }
            if server.type not in supported_protocols:
                compatibility["compatible"] = False
                compatibility["issues"].append(
                    f"Protocol {server.type} not supported by clash"
                )

        elif export_format == "v2ray":
            # Check v2ray compatibility
            supported_protocols = {
                "shadowsocks",
                "vmess",
                "vless",
                "trojan",
                "http",
                "socks",
            }
            if server.type not in supported_protocols:
                compatibility["compatible"] = False
                compatibility["issues"].append(
                    f"Protocol {server.type} not supported by v2ray"
                )

        server.meta["compatibility"] = compatibility

    def _apply_region_preference(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Apply region-based preferences.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
        """
        if "geo" not in server.meta:
            return

        geo_info = server.meta["geo"]
        country = geo_info.get("country", "").upper()

        # Define region categories
        region_info = {"region": "unknown", "region_score": 0.5}

        if country in ["US", "CA"]:
            region_info.update({"region": "north_america", "region_score": 0.9})
        elif country in ["GB", "DE", "FR", "NL", "CH", "SE", "NO"]:
            region_info.update({"region": "europe", "region_score": 0.8})
        elif country in ["JP", "KR", "SG", "HK"]:
            region_info.update({"region": "asia_pacific", "region_score": 0.7})
        elif country in ["CN"]:
            region_info.update({"region": "china", "region_score": 0.4})
        elif country in ["RU"]:
            region_info.update({"region": "russia", "region_score": 0.3})

        server.meta.update(region_info)

    def _apply_usage_hints(
        self, server: ParsedServer, context: PipelineContext, profile: FullProfile
    ) -> None:
        """Apply usage hints based on server characteristics.

        Args:
            server: Server to enrich
            context: Pipeline context
            profile: Full profile configuration
        """
        usage_hints = []

        # Protocol-specific hints
        if server.type == "wireguard":
            usage_hints.append("Excellent for mobile devices")
            usage_hints.append("Best battery life")
        elif server.type in ["vless", "vmess"]:
            usage_hints.append("Good for bypassing DPI")
            usage_hints.append("Supports multiplexing")
        elif server.type == "trojan":
            usage_hints.append("Mimics HTTPS traffic")
            usage_hints.append("Good stealth properties")
        elif server.type == "hysteria2":
            usage_hints.append("Optimized for high-latency networks")
            usage_hints.append("Good for video streaming")

        # Port-specific hints
        if server.port in [80, 8080]:
            usage_hints.append("May work in restrictive networks")
        elif server.port in [443, 8443]:
            usage_hints.append("Appears as HTTPS traffic")

        # Performance-based hints
        if "performance" in server.meta:
            perf_data = server.meta["performance"]

            if perf_data.get("estimated_latency_class") == "low":
                usage_hints.append("Low latency - good for gaming")
            elif perf_data.get("protocol_efficiency") == "high":
                usage_hints.append("High efficiency - good for mobile")

            if perf_data.get("security_level") == "high":
                usage_hints.append("High security level")

        # Security-based hints
        if "security" in server.meta:
            sec_data = server.meta["security"]

            if sec_data.get("encryption_level") == "strong":
                usage_hints.append("Strong encryption")
            elif sec_data.get("port_classification") == "system":
                usage_hints.append("May require elevated privileges")

        if usage_hints:
            server.meta["usage_hints"] = usage_hints
