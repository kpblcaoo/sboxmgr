import os
from unittest.mock import MagicMock, patch

import pytest

from sboxmgr.subscription.fetchers.url_fetcher import URLFetcher
from sboxmgr.subscription.models import SubscriptionSource
from sboxmgr.utils.env import get_fetch_timeout


class TestURLFetcherTimeout:
    """Tests for URLFetcher timeout configuration."""

    def test_default_timeout(self):
        """Test that default timeout is 30 seconds."""
        assert get_fetch_timeout() == 30

    def test_environment_timeout_valid(self):
        """Test that environment variable sets timeout correctly."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "60"}):
            assert get_fetch_timeout() == 60

    def test_environment_timeout_invalid(self):
        """Test that invalid environment timeout falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "invalid"}):
            assert get_fetch_timeout() == 30

    def test_environment_timeout_empty(self):
        """Test that empty environment timeout falls back to default."""
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": ""}):
            assert get_fetch_timeout() == 30

    @patch("requests.get")
    def test_fetch_uses_configured_timeout(self, mock_get):
        """Test that fetch method uses the configured timeout."""
        # Arrange
        mock_response = MagicMock()
        mock_response.raw.read.return_value = b"test data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        source = SubscriptionSource(
            url="https://test-timeout-url.com", source_type="url"
        )
        fetcher = URLFetcher(source)

        # Act
        with patch.dict(os.environ, {"SBOXMGR_FETCH_TIMEOUT": "45"}):
            fetcher.fetch(force_reload=True)

        # Assert
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 45

    @patch("requests.get")
    def test_fetch_uses_default_timeout_when_no_env(self, mock_get):
        """Test that fetch method uses default timeout when no env var set."""
        # Arrange
        mock_response = MagicMock()
        mock_response.raw.read.return_value = b"test data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        source = SubscriptionSource(
            url="https://test-unique-url.com", source_type="url"
        )
        fetcher = URLFetcher(source)

        # Act - ensure no env var is set and force reload to bypass cache
        with patch.dict(os.environ, {}, clear=True):
            fetcher.fetch(force_reload=True)

        # Assert
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 30

    def test_size_limit_method_exists(self):
        """Test that _get_size_limit method is available (regression test)."""
        source = SubscriptionSource(url="https://example.com", source_type="url")
        fetcher = URLFetcher(source)

        # This should not raise AttributeError
        size_limit = fetcher._get_size_limit()
        assert isinstance(size_limit, int)
        assert size_limit > 0

    @patch("requests.get")
    def test_fetch_calls_size_limit_without_error(self, mock_get):
        """Test that fetch method can call _get_size_limit without AttributeError."""
        # Arrange
        mock_response = MagicMock()
        mock_response.raw.read.return_value = b"test data"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        source = SubscriptionSource(url="https://example.com", source_type="url")
        fetcher = URLFetcher(source)

        # Act - this should not raise AttributeError
        try:
            fetcher.fetch()
        except AttributeError as e:
            if "_get_size_limit" in str(e):
                pytest.fail(f"AttributeError related to _get_size_limit: {e}")
        except Exception:
            # Other exceptions are fine for this test
            pass
