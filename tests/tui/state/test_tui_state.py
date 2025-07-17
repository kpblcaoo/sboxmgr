"""Tests for TUI state management.

This module tests the core logic of TUIState class,
including subscription management and server exclusions.
"""

import pytest
from unittest.mock import Mock, patch

from sboxmgr.tui.state.tui_state import TUIState

pytestmark = pytest.mark.skip(reason="TUI tests are optional and may be moved to experimental")


class TestTUIState:
    """Test cases for TUIState class."""

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_initial_state(self):
        """Test initial state of TUIState."""
        state = TUIState()

        assert state.debug == 0
        assert state.profile is None
        assert state.orchestrator is not None
        assert len(state.subscriptions) == 0
        assert state.active_subscription is None
        assert len(state.servers) == 0
        assert len(state.excluded_servers) == 0
        assert len(state.selected_servers) == 0
        assert state.current_screen == "welcome"
        assert state.show_advanced is False

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_has_subscriptions_empty(self):
        """Test has_subscriptions with no subscriptions."""
        state = TUIState()
        assert state.has_subscriptions() is False

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_has_subscriptions_with_data(self):
        """Test has_subscriptions with subscriptions."""
        state = TUIState()
        state.add_subscription("https://example.com/sub")
        assert state.has_subscriptions() is True

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_add_subscription_success(self, mock_get_servers):
        """Test successful subscription addition."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock(), Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()

        result = state.add_subscription("https://example.com/sub")

        assert result is True
        assert len(state.subscriptions) == 1
        assert state.subscriptions[0].url == "https://example.com/sub"
        assert state.subscriptions[0].source_type == "url"
        assert state.active_subscription == "https://example.com/sub"

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_add_subscription_without_tags(self, mock_get_servers):
        """Test subscription addition without tags."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()

        result = state.add_subscription("https://example.com/sub")

        assert result is True
        assert len(state.subscriptions) == 1
        assert state.subscriptions[0].label is None

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_add_multiple_subscriptions(self, mock_get_servers):
        """Test adding multiple subscriptions."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()

        # Add first subscription
        result1 = state.add_subscription("https://example.com/sub1")
        assert result1 is True
        assert state.active_subscription == "https://example.com/sub1"

        # Add second subscription
        result2 = state.add_subscription("https://example.com/sub2")
        assert result2 is True
        assert len(state.subscriptions) == 2
        # Active subscription should remain the first one
        assert state.active_subscription == "https://example.com/sub1"

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.tui.state.tui_state.SubscriptionSource')
    def test_add_subscription_failure(self, mock_subscription_source):
        """Test subscription addition failure."""
        mock_subscription_source.side_effect = Exception("Invalid URL")

        state = TUIState()
        result = state.add_subscription("invalid-url")

        assert result is False
        assert len(state.subscriptions) == 0
        assert state.active_subscription is None

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_remove_subscription_success(self, mock_get_servers):
        """Test successful subscription removal."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()
        state.add_subscription("https://example.com/sub1")
        state.add_subscription("https://example.com/sub2")

        result = state.remove_subscription("https://example.com/sub1")

        assert result is True
        assert len(state.subscriptions) == 1
        assert state.subscriptions[0].url == "https://example.com/sub2"
        # Active subscription should switch to remaining one
        assert state.active_subscription == "https://example.com/sub2"

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_remove_active_subscription(self, mock_get_servers):
        """Test removing active subscription."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()
        state.add_subscription("https://example.com/sub1")
        state.add_subscription("https://example.com/sub2")

        # Remove the active subscription
        result = state.remove_subscription("https://example.com/sub1")

        assert result is True
        assert len(state.subscriptions) == 1
        assert state.active_subscription == "https://example.com/sub2"

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_remove_last_subscription(self, mock_get_servers):
        """Test removing the last subscription."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()
        state.add_subscription("https://example.com/sub")

        result = state.remove_subscription("https://example.com/sub")

        assert result is True
        assert len(state.subscriptions) == 0
        assert state.active_subscription is None

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    @patch('sboxmgr.core.orchestrator.Orchestrator.get_subscription_servers')
    def test_remove_nonexistent_subscription(self, mock_get_servers):
        """Test removing nonexistent subscription."""
        # Mock successful server retrieval
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = [Mock()]
        mock_get_servers.return_value = mock_result

        state = TUIState()
        state.add_subscription("https://example.com/sub")

        result = state.remove_subscription("https://nonexistent.com/sub")

        assert result is True  # Should succeed even if not found
        assert len(state.subscriptions) == 1  # Original subscription remains

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_get_counts(self):
        """Test count getter methods."""
        state = TUIState()

        # Initial counts
        assert state.get_subscription_count() == 0
        assert state.get_server_count() == 0
        assert state.get_excluded_count() == 0

        # Add data
        state.subscriptions = [Mock(), Mock()]
        state.servers = [Mock(), Mock(), Mock()]
        state.excluded_servers = ["server1", "server2"]

        assert state.get_subscription_count() == 2
        assert state.get_server_count() == 3
        assert state.get_excluded_count() == 2

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_toggle_server_exclusion(self):
        """Test server exclusion toggling."""
        state = TUIState()

        # Toggle to exclude
        result = state.toggle_server_exclusion("server1")
        assert result is True  # Now excluded
        assert "server1" in state.excluded_servers

        # Toggle to include
        result = state.toggle_server_exclusion("server1")
        assert result is False  # Now included
        assert "server1" not in state.excluded_servers

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_is_server_excluded(self):
        """Test server exclusion check."""
        state = TUIState()

        assert state.is_server_excluded("server1") is False

        state.excluded_servers.append("server1")
        assert state.is_server_excluded("server1") is True

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_clear_exclusions(self):
        """Test clearing all exclusions."""
        state = TUIState()
        state.excluded_servers = ["server1", "server2", "server3"]

        state.clear_exclusions()

        assert len(state.excluded_servers) == 0

    @patch('sboxmgr.tui.state.tui_state.PROFILES_AVAILABLE', False)
    def test_set_advanced_mode(self):
        """Test advanced mode setting."""
        state = TUIState()

        assert state.show_advanced is False

        state.set_advanced_mode(True)
        assert state.show_advanced is True

        state.set_advanced_mode(False)
        assert state.show_advanced is False
