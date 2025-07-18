"""Template for test fetcher plugin (for sboxmgr plugin system).

This file provides a template for creating test fetcher plugins.
"""

import pytest

from sboxmgr.subscription.fetchers.testfetcher import TestFetcher


def test_testfetcher_basic():
    """Test basic TestFetcher functionality."""
    # Example: instantiate and check NotImplementedError
    plugin = TestFetcher()
    with pytest.raises(NotImplementedError):
        plugin.fetch(None)
