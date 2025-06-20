from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseParser(ABC):
    @abstractmethod
    def parse(self, raw: bytes) -> List[ParsedServer]:
        """Распарсить подписку (raw bytes) в список ParsedServer."""
        pass 