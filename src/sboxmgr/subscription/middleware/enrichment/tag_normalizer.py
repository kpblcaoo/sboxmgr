"""Tag normalization middleware for consistent server naming.

This module provides tag normalization functionality to ensure consistent
server naming across different parsers and data sources.
"""

from typing import List

from ...models import ParsedServer, PipelineContext


class EnrichmentTagNormalizer:
    """Enrichment-specific tag normalizer for consistent naming across parsers.

    Ensures that all servers have consistent tag naming regardless of
    the source parser or data format. Prioritizes human-readable names
    over technical identifiers.
    """

    def __init__(self, prefer_names: bool = True):
        """Initialize tag normalizer.

        Args:
            prefer_names: Whether to prefer human-readable names over technical IDs
        """
        self.prefer_names = prefer_names

    def process(
        self, servers: List[ParsedServer], context: PipelineContext
    ) -> List[ParsedServer]:
        """Normalize tags for all servers.

        Args:
            servers: List of servers to normalize
            context: Pipeline context

        Returns:
            List of servers with normalized tags
        """
        for server in servers:
            server.tag = self._normalize_tag(server)

        return servers

    def _normalize_tag(self, server: ParsedServer) -> str:
        """Normalize tag for a single server.

        Args:
            server: Server to normalize tag for

        Returns:
            Normalized tag string
        """
        # Priority order for tag sources
        tag_sources = []

        if self.prefer_names:
            # Prefer human-readable names
            tag_sources = [
                server.meta.get("name"),  # Human-readable name
                server.meta.get("tag"),  # Original tag
                server.tag,  # Server tag attribute
                f"{server.type}-{server.address}",  # Generated fallback
            ]
        else:
            # Prefer technical identifiers
            tag_sources = [
                server.tag,  # Server tag attribute
                server.meta.get("tag"),  # Original tag
                server.meta.get("name"),  # Human-readable name
                f"{server.type}-{server.address}",  # Generated fallback
            ]

        # Find first non-empty, non-None tag
        for tag_source in tag_sources:
            if tag_source and str(tag_source).strip():
                normalized_tag = str(tag_source).strip()

                # Clean up the tag (remove extra spaces, etc.)
                normalized_tag = " ".join(normalized_tag.split())

                return normalized_tag

        # Fallback to generated tag
        return f"{server.type}-{server.address}"
