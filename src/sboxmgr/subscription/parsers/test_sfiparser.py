
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.parsers.sfiparser import SfiParser

def test_sfiparser_basic():
    # Example: instantiate and check NotImplementedError
    plugin = SfiParser()
    with pytest.raises(NotImplementedError):
        plugin.parse(b"test")
