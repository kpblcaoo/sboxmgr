
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.postprocessors.geofilterpostprocessor import GeoFilterPostProcessor

def test_geofilterpostprocessor_basic():
    # Example: instantiate and check NotImplementedError
    plugin = GeoFilterPostProcessor()
    with pytest.raises(NotImplementedError):
        plugin.process([], None)
