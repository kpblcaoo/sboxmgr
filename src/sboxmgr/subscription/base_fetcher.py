from abc import ABC, abstractmethod
from .models import SubscriptionSource

class BaseFetcher(ABC):
    def __init__(self, source: SubscriptionSource):
        self.source = source

    @abstractmethod
    def fetch(self) -> bytes:
        """Загрузить подписку (raw bytes)."""
        pass 