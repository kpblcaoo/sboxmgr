
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.validators.geovalidator import GeoValidator

def test_geovalidator_basic():
    # Example: instantiate and check NotImplementedError
    plugin = GeoValidator()
    with pytest.raises(NotImplementedError):
        plugin.validate(b"test")
