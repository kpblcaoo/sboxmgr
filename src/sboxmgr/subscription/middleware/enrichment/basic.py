"""Basic enrichment functionality for server data."""

import hashlib
import time

from ...models import ParsedServer, PipelineContext


class BasicEnricher:
    """Provides basic metadata enrichment for servers.

    Adds fundamental metadata like timestamps, identifiers, and trace information
    that are useful for all types of server processing.

    Note: Tag normalization is handled by TagNormalizer middleware.
    This enricher focuses only on basic metadata enrichment.
    """

    def __init__(self):
        """Initialize basic enricher."""
        pass

    def enrich(self, server: ParsedServer, context: PipelineContext) -> ParsedServer:
        """Apply basic metadata enrichment to a server.

        Args:
            server: Server to enrich
            context: Pipeline context

        Returns:
            Server with basic enrichment applied
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

        # Note: Tag normalization is handled by TagNormalizer middleware
        # This enricher preserves existing tags without modification

        return server
