from abc import ABC, abstractmethod
from .models import ParsedServer
from typing import List

class BaseSelector(ABC):
    @abstractmethod
    def select(self, servers: List[ParsedServer], policy: str = None) -> List[ParsedServer]:
        """Выбрать серверы по заданной политике (например, urltest, random, manual)."""
        pass 