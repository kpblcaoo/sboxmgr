"""Base postprocessor interface for subscription data enhancement.

This module defines the abstract base class for postprocessors that enhance
or transform parsed server data after parsing. Postprocessors can add
metadata, apply filters, perform optimizations, or implement custom
transformations before final export.
"""
from abc import ABC, abstractmethod
from .models import ParsedServer, PipelineContext
from typing import List
import inspect

class BasePostProcessor(ABC):
    """Abstract base class for subscription data postprocessors.

    Postprocessors transform or enhance parsed server data after the parsing
    stage. They can add geographic information, apply filtering rules,
    optimize server lists, or perform custom transformations.
    """

    plugin_type = "postprocessor"
    @abstractmethod
    def process(self, servers: List[ParsedServer], context: PipelineContext | None = None) -> List[ParsedServer]:
        """Process and transform parsed server data.

        Args:
            servers: List of ParsedServer objects to process.
            context: Pipeline context containing processing configuration.

        Returns:
            List[ParsedServer]: Processed servers after transformation.

        Raises:
            NotImplementedError: If called directly on base class.

        """
        pass

class DedupPostProcessor(BasePostProcessor):
    """Remove duplicate servers based on type, address, port, and tag."""

    def process(self, servers: List[ParsedServer], context: PipelineContext | None = None) -> List[ParsedServer]:
        """Remove duplicate servers from the list.

        Args:
            servers: List of ParsedServer objects to deduplicate.
            context: Pipeline context (unused in this implementation).

        Returns:
            List[ParsedServer]: Deduplicated server list.
        """
        seen = set()
        result = []
        for s in servers:
            key = (s.type, s.address, s.port, getattr(s, 'meta', {}).get('tag'))
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result

class PostProcessorChain(BasePostProcessor):
    """Chain of postprocessor plugins called in sequence to process ParsedServer list.

    Args:
        processors (list[BasePostProcessor]): List of postprocessor plugins applied sequentially.

    Example:
        chain = PostProcessorChain([DedupPostProcessor(), GeoPostProcessor()])
        servers = chain.process(servers)

    """

    def __init__(self, processors: list):
        """Initialize postprocessor chain.

        Args:
            processors: List of postprocessor instances to chain.
        """
        self.processors = processors

    def process(self, servers: List[ParsedServer], context: PipelineContext | None = None) -> List[ParsedServer]:
        """Apply all postprocessor plugins sequentially to the server list.

        Args:
            servers (List[ParsedServer]): Input server list.
            context: Pipeline context containing processing configuration.

        Returns:
            List[ParsedServer]: Result after applying all postprocessor plugins.

        """
        for proc in self.processors:
            sig = inspect.signature(proc.process)
            # Check if the processor accepts context parameter specifically
            has_context_param = 'context' in sig.parameters
            if context is not None and has_context_param:
                servers = proc.process(servers, context=context)
            else:
                servers = proc.process(servers)
        return servers
