"""Tests for SubscriptionManagerScreen."""

import pytest
from unittest.mock import patch

from sboxmgr.tui.screens.subscription_manager import SubscriptionManagerScreen

pytestmark = pytest.mark.skip(reason="TUI tests are optional and may be moved to experimental")


class TestSubscriptionManagerScreen:
    """Test cases for SubscriptionManagerScreen."""

    @pytest.fixture
    def screen(self):
        """Create a SubscriptionManagerScreen instance."""
        return SubscriptionManagerScreen()

    def test_initialization(self, screen):
        """Test screen initialization."""
        assert screen._subscriptions == []
        assert screen._active_subscription == ""

    def test_subscription_url_extraction(self, screen):
        """Test subscription URL extraction."""
        subscription = {"url": "https://example.com/subscription", "tags": ["test"]}
        url = screen._get_subscription_url(subscription)

        assert url == "https://example.com/subscription"

    def test_subscription_display_formatting(self, screen):
        """Test subscription display formatting."""
        subscription = {
            "url": "https://example.com/subscription",
            "tags": ["tag1", "tag2"],
            "type": "vmess"
        }

        display_text = screen._format_subscription_display(subscription)

        assert "https://example.com/subscription" in display_text
        assert "tag1" in display_text or "tag2" in display_text

    @patch.object(SubscriptionManagerScreen, 'app')
    def test_add_subscription_button(self, mock_app, screen):
        """Test add subscription button functionality."""
        screen.on_add_subscription_pressed()

        # Should push subscription form screen
        mock_app.push_screen.assert_called_once()

    @patch.object(SubscriptionManagerScreen, 'app')
    def test_back_button_functionality(self, mock_app, screen):
        """Test back button functionality."""
        screen.on_back_pressed()

        # Should pop screen
        mock_app.pop_screen.assert_called_once()

    @patch.object(SubscriptionManagerScreen, 'app')
    def test_subscription_result_handling_success(self, mock_app, screen):
        """Test successful subscription result handling."""
        screen._handle_subscription_result(True)

        # Should show success notification and reload
        mock_app.notify.assert_called_once()

    @patch.object(SubscriptionManagerScreen, 'app')
    def test_subscription_result_handling_failure(self, mock_app, screen):
        """Test failed subscription result handling."""
        error_message = "Failed to add subscription"
        screen._handle_subscription_result(error_message)

        # Should show error notification
        mock_app.notify.assert_called_once()

    def test_info_panel_with_subscriptions(self, screen):
        """Test info panel creation with subscriptions."""
        screen._subscriptions = [
            {"url": "https://example.com/sub1", "tags": ["tag1"]},
            {"url": "https://example.com/sub2", "tags": ["tag2"]}
        ]
        screen._active_subscription = "https://example.com/sub1"

        info_panel = screen._create_info_panel()

        # Should create static widget with subscription info
        assert info_panel is not None

    def test_info_panel_without_subscriptions(self, screen):
        """Test info panel creation without subscriptions."""
        screen._subscriptions = []

        info_panel = screen._create_info_panel()

        # Should create static widget with no subscriptions message
        assert info_panel is not None
