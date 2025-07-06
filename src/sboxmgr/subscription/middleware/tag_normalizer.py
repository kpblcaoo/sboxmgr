"""
Tag normalization middleware for consistent server naming.

This module provides centralized tag normalization logic to ensure
consistent server naming across all User-Agent types and parsers.
"""

import re
from typing import Any, Dict, List, Optional, Set

from ...configs.models import FullProfile
from ..models import ParsedServer, PipelineContext
from .base import BaseMiddleware


class TagNormalizer(BaseMiddleware):
    """
    Middleware for normalizing server tags with priority-based selection.

    Priority order:
    1. meta['name'] (human-readable from source)
    2. meta['tag'] (explicit tag from source)
    3. tag (parser-generated tag)
    4. address (IP/domain fallback)
    5. protocol-based fallback
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._used_tags: Set[str] = set()

    def process(
        self,
        servers: List[ParsedServer],
        context: PipelineContext,
        profile: Optional[FullProfile] = None,
    ) -> List[ParsedServer]:
        """
        Process servers to normalize their tags.

        Args:
            servers: List of server models to process
            context: Pipeline context
            profile: Full profile configuration

        Returns:
            List of servers with normalized tags
        """
        self._used_tags.clear()

        for server in servers:
            original_tag = server.tag
            normalized_tag = self._normalize_tag(server)

            # Ensure uniqueness
            unique_tag = self._ensure_unique_tag(normalized_tag)
            server.tag = unique_tag

            # Log tag changes for debugging
            if original_tag != unique_tag:
                # Note: logging would need proper logger setup
                pass

        return servers

    def _normalize_tag(self, server: ParsedServer) -> str:
        """
        Normalize a single server's tag based on priority.

        Args:
            server: Server model to normalize

        Returns:
            Normalized tag string
        """
        # Priority 1: meta['name'] (human-readable from source)
        if server.meta and server.meta.get("name"):
            name = server.meta["name"]
            if isinstance(name, str) and name.strip():
                return self._sanitize_tag(name.strip())

        # Priority 2: meta['label'] (human-readable from source - alternative field)
        if server.meta and server.meta.get("label"):
            label = server.meta["label"]
            if isinstance(label, str) and label.strip():
                return self._sanitize_tag(label.strip())

        # Priority 3: meta['tag'] (explicit tag from source)
        if server.meta and server.meta.get("tag"):
            tag = server.meta["tag"]
            if isinstance(tag, str) and tag.strip():
                return self._sanitize_tag(tag.strip())

        # Priority 4: tag (parser-generated tag)
        if server.tag and server.tag.strip():
            return self._sanitize_tag(server.tag.strip())

        # Priority 5: address (IP/domain fallback)
        if server.address:
            return f"{server.type}-{server.address}"

        # Priority 6: protocol-based fallback
        return f"{server.type}-{id(server)}"

    def _sanitize_tag(self, tag: str) -> str:
        """
        Sanitize tag to ensure it's valid for various formats (JSON, YAML, etc.).

        Args:
            tag: Raw tag string

        Returns:
            Sanitized tag string
        """
        # Only remove control characters and normalize whitespace
        # Keep all printable characters including emojis, symbols, etc.
        sanitized = re.sub(r"[\x00-\x1f\x7f]", "", tag)  # Remove control chars only

        # Normalize whitespace (collapse multiple spaces, trim)
        sanitized = re.sub(r"\s+", " ", sanitized)
        sanitized = sanitized.strip()

        # Ensure non-empty
        if not sanitized:
            return "unnamed-server"

        return sanitized

    def _ensure_unique_tag(self, tag: str) -> str:
        """
        Ensure tag is unique by appending suffix if needed.

        Args:
            tag: Base tag string

        Returns:
            Unique tag string
        """
        if tag not in self._used_tags:
            self._used_tags.add(tag)
            return tag

        # Find unique suffix using parentheses (safe for JSON/YAML)
        counter = 1
        while f"{tag} ({counter})" in self._used_tags:
            counter += 1

        unique_tag = f"{tag} ({counter})"
        self._used_tags.add(unique_tag)
        return unique_tag
