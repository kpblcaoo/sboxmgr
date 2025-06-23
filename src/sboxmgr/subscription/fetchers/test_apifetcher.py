
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.fetchers.apifetcher import ApiFetcher

def test_apifetcher_basic():
    # Example: instantiate and check NotImplementedError
    plugin = ApiFetcher()
    with pytest.raises(NotImplementedError):
        plugin.fetch(None)
