from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseExporter(ABC):
    @abstractmethod
    def export(self, servers: List[ParsedServer]) -> str:
        """Экспортировать список ParsedServer в строку (например, JSON, YAML)."""
        pass 