
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.fetchers.mytestfetcher import MyTestFetcher

def test_mytestfetcher_basic():
    # Example: instantiate and check NotImplementedError
    plugin = MyTestFetcher()
    with pytest.raises(NotImplementedError):
        plugin.fetch(None)
