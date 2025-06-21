from abc import ABC, abstractmethod
from .models import SubscriptionSource
from typing import Any

class BaseAuthHandler(ABC):
    """Интерфейс для генерации заголовков/токенов для защищённых API (будущее)."""
    @abstractmethod
    def get_auth_headers(self, source: SubscriptionSource) -> dict:
        pass

class BaseHeaderPlugin(ABC):
    """Интерфейс для добавления/модификации заголовков (будущее)."""
    @abstractmethod
    def process_headers(self, headers: dict, source: SubscriptionSource) -> dict:
        pass

class BaseFetcher(ABC):
    def __init__(self, source: SubscriptionSource):
        self.source = source
        self.auth_handler: BaseAuthHandler | None = None
        self.header_plugins: list[BaseHeaderPlugin] = []

    @abstractmethod
    def fetch(self) -> bytes:
        """Загрузить подписку (raw bytes)."""
        pass 