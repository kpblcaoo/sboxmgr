import requests
from ..models import SubscriptionSource
from ..base_fetcher import BaseFetcher
from ..registry import register

@register("url_json")
class JSONFetcher(BaseFetcher):
    def fetch(self) -> bytes:
        if self.source.url.startswith("file://"):
            path = self.source.url.replace("file://", "", 1)
            with open(path, "rb") as f:
                return f.read()
        else:
            resp = requests.get(self.source.url)
            resp.raise_for_status()
            return resp.content 