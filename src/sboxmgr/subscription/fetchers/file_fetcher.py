from ..models import SubscriptionSource
from ..base_fetcher import BaseFetcher
from ..registry import register

@register("file")
class FileFetcher(BaseFetcher):
    def fetch(self) -> bytes:
        path = self.source.url.replace("file://", "", 1)
        with open(path, "rb") as f:
            return f.read() 