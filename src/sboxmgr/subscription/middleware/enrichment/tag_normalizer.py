"""Tag normalization middleware for consistent server naming.

This module provides tag normalization functionality to ensure consistent
server naming across different parsers and data sources.
"""

from typing import List

from ...models import ParsedServer, PipelineContext


class EnrichmentTagNormalizer:
    """Enrichment-specific tag normalizer for consistent naming across parsers.

    Priority order:
    1. meta['name'] (human-readable from source)
    2. meta['label'] (alternative human-readable label)
    3. meta['tag'] (explicit tag from source)
    4. tag (parser-generated tag)
    5. address (IP/domain fallback)
    6. protocol-based fallback (type + object id)
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
        # Priority 1: meta['name']
        if server.meta and server.meta.get("name"):
            name = server.meta["name"]
            if isinstance(name, str) and name.strip():
                return self._sanitize_tag(name.strip())

        # Priority 2: meta['label']
        if server.meta and server.meta.get("label"):
            label = server.meta["label"]
            if isinstance(label, str) and label.strip():
                return self._sanitize_tag(label.strip())

        # Priority 3: meta['tag']
        if server.meta and server.meta.get("tag"):
            tag = server.meta["tag"]
            if isinstance(tag, str) and tag.strip():
                return self._sanitize_tag(tag.strip())

        # Priority 4: tag (parser-generated)
        if server.tag and server.tag.strip():
            return self._sanitize_tag(server.tag.strip())

        # Priority 5: address fallback (only if not None and not empty)
        if server.address is not None and str(server.address).strip() != "":
            return f"{server.type}-{server.address}"

        # Priority 6: protocol-based fallback (if address is empty or None)
        return f"{server.type}-{id(server)}"

    def _sanitize_tag(self, tag: str) -> str:
        """Sanitize a tag string.

        Args:
            tag: The tag string to sanitize

        Returns:
            Sanitized tag string
        """
        # Remove control characters and normalize whitespace
        import re

        sanitized = re.sub(r"[\x00-\x1f\x7f]", "", tag)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        if not sanitized:
            return "unnamed-server"
        return sanitized
