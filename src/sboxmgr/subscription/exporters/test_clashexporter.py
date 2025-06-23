
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.exporters.clashexporter import ClashExporter

def test_clashexporter_basic():
    # Example: instantiate and check NotImplementedError
    plugin = ClashExporter()
    with pytest.raises(NotImplementedError):
        plugin.export([])
