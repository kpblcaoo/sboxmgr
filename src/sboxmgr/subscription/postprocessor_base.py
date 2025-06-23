from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BasePostProcessor(ABC):
    """BasePostProcessor: абстрактный класс для postprocessor-плагинов.
    plugin_type = "postprocessor" для автодокументации и фильтрации.
    """
    plugin_type = "postprocessor"
    @abstractmethod
    def process(self, servers: List[ParsedServer]) -> List[ParsedServer]:
        """Обработать/фильтровать список ParsedServer (dedup, geo, latency и т.д.)."""
        pass

class DedupPostProcessor(BasePostProcessor):
    def process(self, servers: List[ParsedServer]) -> List[ParsedServer]:
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

    def process(self, servers: List[ParsedServer]) -> List[ParsedServer]:
        """Применить все postprocessor-плагины по очереди к списку серверов.

        Args:
            servers (List[ParsedServer]): Входной список серверов.

        Returns:
            List[ParsedServer]: Результат после применения всех postprocessor-плагинов.
        """
        for proc in self.processors:
            servers = proc.process(servers)
        return servers 