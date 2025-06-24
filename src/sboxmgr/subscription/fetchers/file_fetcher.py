from pathlib import Path
from ..models import SubscriptionSource
from ..base_fetcher import BaseFetcher
from ..registry import register
import threading

@register("file")
class FileFetcher(BaseFetcher):
    SUPPORTED_SCHEMES = ("file",)
    _cache_lock = threading.Lock()
    _fetch_cache = {}

    def __init__(self, source: SubscriptionSource):
        super().__init__(source)

    def fetch(self, force_reload: bool = False) -> bytes:
        """Загружает данные из локального файла с кешированием и проверкой размера.

        Args:
            force_reload (bool, optional): Принудительно сбросить кеш и заново получить результат.

        Returns:
            bytes: Содержимое файла.

        Raises:
            ValueError: Если размер файла превышает лимит.
            FileNotFoundError: Если файл не найден.
        """
        key = (self.source.url,)
        if force_reload:
            with self._cache_lock:
                self._fetch_cache.pop(key, None)
        with self._cache_lock:
            if key in self._fetch_cache:
                return self._fetch_cache[key]
        
        # Убираем схему file:// из URL
        path_str = self.source.url.replace("file://", "", 1)
        path = Path(path_str)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Проверяем размер файла перед чтением
        file_size = path.stat().st_size
        size_limit = self._get_size_limit()
        
        if file_size > size_limit:
            raise ValueError(f"File size ({file_size} bytes) exceeds limit ({size_limit} bytes)")
        
        with open(path, "rb") as f:
            data = f.read()
            
        with self._cache_lock:
            self._fetch_cache[key] = data
        return data

    @classmethod
    def validate_url_scheme(cls, url: str):
        """Валидирует схему URL для FileFetcher."""
        if not url.startswith("file://"):
            raise ValueError(f"FileFetcher supports only file:// URLs, got: {url}")

 