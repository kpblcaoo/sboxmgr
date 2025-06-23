import os
from ..models import SubscriptionSource
from ..base_fetcher import BaseFetcher
from ..registry import register
import threading

@register("file")
class FileFetcher(BaseFetcher):
    _cache_lock = threading.Lock()
    _fetch_cache = {}

    def __init__(self, source: SubscriptionSource):
        super().__init__(source)  # SEC: centralized scheme validation

    def fetch(self, force_reload: bool = False) -> bytes:
        """Загружает подписку из локального файла с поддержкой лимита размера и in-memory кешированием.

        Args:
            force_reload (bool, optional): Принудительно сбросить кеш и заново получить результат.

        Returns:
            bytes: Сырые данные подписки.

        Raises:
            ValueError: Если размер файла превышает лимит.
        """
        key = (self.source.url,)
        if force_reload:
            with self._cache_lock:
                self._fetch_cache.pop(key, None)
        with self._cache_lock:
            if key in self._fetch_cache:
                return self._fetch_cache[key]
        size_limit = self._get_size_limit()
        path = self.source.url.replace("file://", "", 1)
        with open(path, "rb") as f:
            data = f.read(size_limit + 1)
            if len(data) > size_limit:
                print(f"[fetcher][WARN] File size exceeds limit ({size_limit} bytes), skipping.")
                raise ValueError("File size exceeds limit")
            with self._cache_lock:
                self._fetch_cache[key] = data
            return data

    def _get_size_limit(self) -> int:
        """Возвращает лимит размера входных данных в байтах (по умолчанию 2 MB)."""
        env_limit = os.getenv("SBOXMGR_FETCH_SIZE_LIMIT")
        if env_limit:
            try:
                return int(env_limit)
            except Exception:
                pass
        # TODO: добавить чтение из config.toml
        return 2 * 1024 * 1024 