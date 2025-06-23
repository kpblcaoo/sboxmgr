
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.postprocessors.geofilterpostprocessorpostprocessor import GeoFilterPostProcessorPostprocessor

def test_geofilterpostprocessorpostprocessor_basic():
    # Example: instantiate and check NotImplementedError
    plugin = GeoFilterPostProcessorPostprocessor()
    with pytest.raises(NotImplementedError):
        plugin.process([], None)
