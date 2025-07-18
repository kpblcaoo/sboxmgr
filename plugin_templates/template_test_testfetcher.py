# This is a template file - copy to your test directory and modify as needed
import pytest
from sboxmgr.subscription.fetchers.testfetcher import TestFetcher


def test_testfetcher_basic():
    """Test basic TestFetcher functionality."""
    # Example: instantiate and check NotImplementedError
    plugin = TestFetcher()
    with pytest.raises(NotImplementedError):
        plugin.fetch(None)
