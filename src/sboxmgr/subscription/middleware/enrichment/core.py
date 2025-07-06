"""Core enrichment middleware implementation."""

import time
from typing import Any, Dict, List, Optional

from ....configs.models import FullProfile
from ...models import ParsedServer, PipelineContext
from ..base import TransformMiddleware
from .basic import BasicEnricher
from .custom import CustomEnricher
from .geo import GeoEnricher
from .performance import PerformanceEnricher
from .security import SecurityEnricher
from .tag_normalizer import TagNormalizer


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

        # Configuration
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

        # Initialize enrichers
        self.basic_enricher = BasicEnricher()
        self.tag_normalizer = TagNormalizer(prefer_names=True)
        self.geo_enricher = GeoEnricher(self.geo_database_path)
        self.performance_enricher = PerformanceEnricher(self.performance_cache_duration)
        self.security_enricher = SecurityEnricher()
        self.custom_enricher = CustomEnricher(self.custom_enrichers)

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
                # Apply enrichment
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
        if (
            hasattr(profile, "metadata")
            and profile.metadata
            and "enrichment" in profile.metadata
        ):
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

        # Apply basic metadata enrichment (always enabled)
        server = self.basic_enricher.enrich(server, context)

        # Apply tag normalization (always enabled)
        server.tag = self.tag_normalizer._normalize_tag(server)

        # Apply geographic enrichment
        if enrichment_config["enable_geo_enrichment"]:
            server = self.geo_enricher.enrich(server, context)

        # Apply performance enrichment
        if enrichment_config["enable_performance_enrichment"]:
            server = self.performance_enricher.enrich(server, context)

        # Apply security enrichment
        if enrichment_config["enable_security_enrichment"]:
            server = self.security_enricher.enrich(server, context)

        # Apply custom enrichment
        if enrichment_config["enable_custom_enrichment"]:
            server = self.custom_enricher.enrich(
                server, context, profile, enrichment_config["custom_enrichers"]
            )

        return server
