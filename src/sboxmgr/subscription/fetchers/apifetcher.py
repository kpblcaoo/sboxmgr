"""API-based subscription fetcher implementation.

This module provides the APIFetcher class for retrieving subscription data
from API endpoints with authentication, rate limiting, and error handling.
It supports various authentication methods and provides robust error recovery
for production API integrations.
"""

from ..base_fetcher import BaseFetcher
from ..registry import register


@register("custom_fetcher")
class ApiFetcher(BaseFetcher):
    """ApiFetcher fetches subscription data.

    Example:
    fetcher = ApiFetcher(source)
    data = fetcher.fetch()

    """

    def fetch(self, force_reload: bool = False) -> bytes:
        """Fetch subscription data.

        Args:
            force_reload (bool, optional): Force reload and ignore cache.

        Returns:
            bytes: Raw data.

        """
        raise NotImplementedError()
