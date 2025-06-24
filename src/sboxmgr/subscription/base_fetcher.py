from abc import ABC, abstractmethod
from .models import SubscriptionSource
from typing import Any
import os
from urllib.parse import urlparse

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
    """BaseFetcher: абстрактный класс для fetcher-плагинов.
    plugin_type = "fetcher" для автодокументации и фильтрации.
    """
    plugin_type = "fetcher"
    SUPPORTED_SCHEMES = ("http", "https", "file")

    def __init__(self, source: SubscriptionSource):
        self.source = source
        self.auth_handler: BaseAuthHandler | None = None
        self.header_plugins: list[BaseHeaderPlugin] = []
        self.validate_url_scheme(self.source.url)

    @classmethod
    def validate_url_scheme(cls, url: str):
        scheme = urlparse(url).scheme
        if scheme not in cls.SUPPORTED_SCHEMES:
            raise ValueError(f"unsupported scheme: {scheme}")

    @abstractmethod
    def fetch(self) -> bytes:
        """Загрузить подписку (raw bytes)."""
        pass

    def _get_size_limit(self) -> int:
        """Возвращает лимит размера входных данных в байтах (по умолчанию 2 MB).

        Можно переопределить в наследнике для специфичных fetcher'ов.
        Используйте этот метод при чтении файлов/загрузке данных, чтобы обеспечить fail-tolerance и безопасность.
        """
        env_limit = os.getenv("SBOXMGR_FETCH_SIZE_LIMIT")
        if env_limit:
            try:
                return int(env_limit)
            except Exception:
                pass
        # TODO: добавить чтение из config.toml
        return 2 * 1024 * 1024 