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
    def process(self, servers: List[ParsedServer], context: PipelineContext | None = None) -> List[ParsedServer]:
        seen = set()
        result = []
        for s in servers:
            key = (s.type, s.address, s.port, getattr(s, 'meta', {}).get('tag'))
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result 

class PostProcessorChain(BasePostProcessor):
    """Цепочка postprocessor-плагинов, вызываемых по порядку для обработки списка ParsedServer.

    Args:
        processors (list[BasePostProcessor]): Список postprocessor-плагинов, применяемых по очереди.

    Пример:
        chain = PostProcessorChain([DedupPostProcessor(), GeoPostProcessor()])
        servers = chain.process(servers)
    """
    def __init__(self, processors: list):
        self.processors = processors

    def process(self, servers: List[ParsedServer], context: PipelineContext | None = None) -> List[ParsedServer]:
        """Применить все postprocessor-плагины по очереди к списку серверов.

        Args:
            servers (List[ParsedServer]): Входной список серверов.
            context: Pipeline context containing processing configuration.

        Returns:
            List[ParsedServer]: Результат после применения всех postprocessor-плагинов.
        """
        for proc in self.processors:
            sig = inspect.signature(proc.process)
            if context is not None and len(sig.parameters) >= 3:
                servers = proc.process(servers, context)
            else:
                servers = proc.process(servers)
        return servers 