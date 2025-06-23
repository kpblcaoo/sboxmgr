
import pytest
from sboxmgr.subscription.models import SubscriptionSource, ParsedServer
from sboxmgr.subscription.parsed_validators.mytestparsedparsedvalidator import MyTestParsedParsedValidator

def test_mytestparsedparsedvalidator_basic():
    # Example: instantiate and check NotImplementedError
    plugin = MyTestParsedParsedValidator()
    with pytest.raises(NotImplementedError):
        plugin.validate(b"test", None)
