from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseParser(ABC):
    """BaseParser: абстрактный класс для parser-плагинов.
    plugin_type = "parser" для автодокументации и фильтрации.
    """
    plugin_type = "parser"
    @abstractmethod
    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Распарсить подписку (raw bytes) в список ParsedServer."""
        pass 