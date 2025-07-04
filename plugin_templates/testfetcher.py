from ..registry import register
from ..base_fetcher import BaseFetcher
from ..models import SubscriptionSource, ParsedServer


@register("custom_fetcher")
class TestFetcher(BaseFetcher):
    """TestFetcher fetches subscription data from custom source.

    This fetcher implements the BaseFetcher interface to retrieve subscription
    data from a custom source. Customize the fetch method to implement your
    specific data retrieval logic.

    Example:
        source = SubscriptionSource(url="custom://example", source_type="custom_fetcher")
        fetcher = TestFetcher(source)
        data = fetcher.fetch()
    """

    def fetch(self, force_reload: bool = False) -> bytes:
        """Fetch subscription data from the configured source.

        Args:
            force_reload: Whether to bypass cache and force fresh data retrieval.

        Returns:
            Raw subscription data as bytes.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("Implement your custom fetch logic here")
