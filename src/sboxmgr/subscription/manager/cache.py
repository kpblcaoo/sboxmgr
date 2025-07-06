"""Cache management functionality for subscription manager."""

import threading
from typing import Dict, Tuple, Any

from ..models import PipelineContext


class CacheManager:
    """Manages caching for subscription manager operations.

    Provides thread-safe caching with customizable key generation
    for get_servers operations and other expensive operations.
    """

    def __init__(self):
        """Initialize cache manager with thread safety."""
        self._cache_lock = threading.Lock()
        self._get_servers_cache: Dict[Tuple, Any] = {}

    def create_cache_key(self, mode: str, context: PipelineContext, fetcher_source) -> tuple:
        """Create cache key for get_servers results.

        Generates a unique cache key based on subscription source parameters
        and execution context to ensure proper cache differentiation.

        Args:
            mode: Pipeline execution mode.
            context: Pipeline execution context.
            fetcher_source: Fetcher source object with URL and headers.

        Returns:
            Tuple representing the unique cache key.
        """
        return (
            str(fetcher_source.url),
            getattr(fetcher_source, 'user_agent', None),
            str(getattr(fetcher_source, 'headers', None)),
            str(getattr(context, 'tag_filters', None)),
            str(mode),
        )

    def get_cached_result(self, cache_key: tuple) -> Any:
        """Get cached result by key.

        Args:
            cache_key: Cache key to lookup.

        Returns:
            Cached result or None if not found.
        """
        with self._cache_lock:
            return self._get_servers_cache.get(cache_key)

    def set_cached_result(self, cache_key: tuple, result: Any) -> None:
        """Set cached result for key.

        Args:
            cache_key: Cache key to store under.
            result: Result to cache.
        """
        with self._cache_lock:
            self._get_servers_cache[cache_key] = result

    def clear_cache(self) -> None:
        """Clear all cached results."""
        with self._cache_lock:
            self._get_servers_cache.clear()

    def remove_cached_result(self, cache_key: tuple) -> None:
        """Remove specific cached result.

        Args:
            cache_key: Cache key to remove.
        """
        with self._cache_lock:
            self._get_servers_cache.pop(cache_key, None)

    def get_cache_size(self) -> int:
        """Get current cache size.

        Returns:
            Number of cached items.
        """
        with self._cache_lock:
            return len(self._get_servers_cache)
