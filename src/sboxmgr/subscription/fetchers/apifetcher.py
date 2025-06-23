from ..registry import register
from ..base_fetcher import BaseFetcher
from ..models import SubscriptionSource, ParsedServer


@register("custom_fetcher")
class ApiFetcher(BaseFetcher):
    """ApiFetcher fetches subscription data.

Example:
    fetcher = ApiFetcher(source)
    data = fetcher.fetch()"""
    def fetch(self, force_reload: bool = False) -> bytes:
        """Fetch subscription data.

        Args:
            force_reload (bool, optional): Force reload and ignore cache.

        Returns:
            bytes: Raw data.
        """
        raise NotImplementedError()

