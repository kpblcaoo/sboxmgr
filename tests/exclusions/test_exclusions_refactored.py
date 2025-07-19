"""Tests for subscription exclusions functionality.

These tests ensure that the subscription exclusions commands work correctly
with the new modular CLI structure.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
import typer

from sboxmgr.cli.commands.subscription.exclusions import (
    exclusions_list,
    exclusions_add,
    exclusions_remove,
    exclusions_clear,
    _fetch_and_validate_subscription,
    _cache_server_data,
    _show_usage_help,
)


@pytest.fixture
def supported_protocols():
    """Fixture to provide supported protocols without direct import."""
    from sboxmgr.constants import SUPPORTED_PROTOCOLS
    return SUPPORTED_PROTOCOLS


class TestExclusionsConstants:
    """Test constants and basic imports."""

    def test_supported_protocols_constant(self, supported_protocols):
        """Test that SUPPORTED_PROTOCOLS is defined and accessible."""
        assert isinstance(supported_protocols, tuple)
        assert len(supported_protocols) > 0
        assert "vless" in supported_protocols
        assert "vmess" in supported_protocols
        assert "shadowsocks" in supported_protocols
        assert "trojan" in supported_protocols


class TestExclusionsList:
    """Test exclusions list functionality."""

    @pytest.fixture
    def mock_manager(self):
        """Mock ExclusionManager for testing."""
        manager = MagicMock()
        manager.list_all.return_value = []
        return manager

    def test_exclusions_list_empty_json(self, mock_manager):
        """Test exclusions list with empty exclusions in JSON format."""
        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("builtins.print") as mock_print,
        ):
            exclusions_list(json_output=True)

            expected_output = {"total": 0, "exclusions": []}
            mock_print.assert_called_once_with(json.dumps(expected_output, indent=2))

    def test_exclusions_list_empty_table(self, mock_manager):
        """Test exclusions list with empty exclusions in table format."""
        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("sboxmgr.cli.commands.subscription.exclusions.console.print") as mock_console,
        ):
            exclusions_list(json_output=False)

            mock_console.assert_called_once_with("[dim]📝 No exclusions found.[/dim]")

    def test_exclusions_list_with_data_json(self, mock_manager):
        """Test exclusions list with data in JSON format."""
        exclusions_data = [
            {
                "id": "test-id-123",
                "name": "test-server",
                "reason": "testing",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]
        mock_manager.list_all.return_value = exclusions_data

        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("builtins.print") as mock_print,
        ):
            exclusions_list(json_output=True)

            expected_output = {"total": 1, "exclusions": exclusions_data}
            mock_print.assert_called_once_with(json.dumps(expected_output, indent=2))

    def test_exclusions_list_with_data_table(self, mock_manager):
        """Test exclusions list with data in table format."""
        exclusions_data = [
            {
                "id": "test-id-123456789",
                "name": "test-server",
                "reason": "testing",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]
        mock_manager.list_all.return_value = exclusions_data

        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("sboxmgr.cli.commands.subscription.exclusions.console.print") as mock_console,
        ):
            exclusions_list(json_output=False)

            mock_console.assert_called_once()


class TestExclusionsClear:
    """Test exclusions clear functionality."""

    @pytest.fixture
    def mock_manager(self):
        """Mock ExclusionManager for testing."""
        manager = MagicMock()
        manager.list_all.return_value = []
        manager.clear.return_value = 0
        return manager

    def test_exclusions_clear_confirmed(self, mock_manager):
        """Test exclusions clear with confirmation."""
        mock_manager.clear.return_value = 5
        mock_manager.list_all.return_value = [{"id": "test1"}, {"id": "test2"}]

        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("sboxmgr.cli.commands.subscription.exclusions.Confirm.ask", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            exclusions_clear(json_output=True)

            mock_manager.clear.assert_called_once()
            expected_output = {"action": "clear", "removed_count": 5}
            mock_print.assert_called_once_with(json.dumps(expected_output))

    def test_exclusions_clear_cancelled(self, mock_manager):
        """Test exclusions clear with cancellation."""
        mock_manager.list_all.return_value = [{"id": "test1"}]

        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("sboxmgr.cli.commands.subscription.exclusions.Confirm.ask", return_value=False),
            patch("sboxmgr.cli.commands.subscription.exclusions.console.print") as mock_console,
        ):
            exclusions_clear(json_output=False)

            mock_manager.clear.assert_not_called()
            mock_console.assert_called_once()
            call_args = mock_console.call_args[0][0]
            assert "[yellow]" in call_args

    def test_exclusions_clear_no_exclusions(self, mock_manager):
        """Test exclusions clear when no exclusions exist."""
        mock_manager.list_all.return_value = []

        with (
            patch(
                "sboxmgr.cli.commands.subscription.exclusions.ExclusionManager.default",
                return_value=mock_manager,
            ),
            patch("builtins.print") as mock_print,
        ):
            exclusions_clear(json_output=True)

            expected_output = {
                "action": "clear",
                "removed_count": 0,
                "message": "No exclusions to clear",
            }
            mock_print.assert_called_once_with(json.dumps(expected_output))


class TestHelperFunctions:
    """Test helper functions."""

    def test_show_usage_help(self):
        """Test _show_usage_help function."""
        with patch("sboxmgr.cli.commands.subscription.exclusions.console.print") as mock_console:
            _show_usage_help()

            mock_console.assert_called()
            calls = [call[0][0] for call in mock_console.call_args_list]
            help_call = next((call for call in calls if "[yellow]💡" in call), None)
            assert help_call is not None
            # Should mention the available options
            assert any(
                option in help_call
                for option in ["--add", "--remove", "--view", "--clear", "--list-servers"]
            )

    def test_fetch_and_validate_subscription(self):
        """Test _fetch_and_validate_subscription function."""
        sample_data = {"outbounds": [{"type": "vless", "tag": "test"}]}

        with patch("sboxmgr.cli.commands.subscription.exclusions.fetch_json", return_value=sample_data):
            result = _fetch_and_validate_subscription("http://test.com", False)

            assert result == sample_data

    def test_cache_server_data(self):
        """Test _cache_server_data function."""
        manager = MagicMock()
        json_data = {"outbounds": [{"type": "vless", "tag": "test"}]}

        _cache_server_data(manager, json_data, False)

        manager.set_servers_cache.assert_called_once()
