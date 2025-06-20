from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BasePostProcessor(ABC):
    @abstractmethod
    def process(self, servers: List[ParsedServer]) -> List[ParsedServer]:
        """Обработать/фильтровать список ParsedServer (dedup, geo, latency и т.д.)."""
        pass 