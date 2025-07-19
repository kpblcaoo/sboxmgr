"""Adapted tests for subscription exclusions functionality.

These tests are adapted from the original test_exclusions.py to work with
the new modular CLI structure while preserving all test coverage.
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
from sboxmgr.cli.commands.subscription.exclusions_logic import (
    exclusions_add_logic,
    exclusions_remove_logic,
    exclusions_list_logic,
    exclusions_clear_logic,
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
            patch("sboxmgr.cli.commands.subscription.exclusions_logic.console.print") as mock_console,
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
            patch("sboxmgr.cli.commands.subscription.exclusions_logic.console.print") as mock_console,
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
            patch("rich.prompt.Confirm.ask", return_value=True),
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
            patch("rich.prompt.Confirm.ask", return_value=False),
            patch("sboxmgr.cli.commands.subscription.exclusions_logic.console.print") as mock_console,
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


class TestExclusionsAddLogic:
    """Test the internal exclusions add logic (adapted for new structure)."""

    @pytest.fixture
    def mock_manager(self, supported_protocols):
        """Mock ExclusionManager with server cache."""
        manager = MagicMock()
        manager._servers_cache = {
            "servers": [{"type": "vless", "tag": "test1"}, {"type": "vmess", "tag": "test2"}],
            "supported_protocols": supported_protocols,
            "supported_servers": [{"type": "vless"}, {"type": "vmess"}],
        }
        manager.add_by_index.return_value = ["test-id-1"]
        manager.add_by_wildcard.return_value = ["test-id-2"]
        manager.has_servers_cache.return_value = True
        return manager

    def test_exclusions_add_logic_by_index(self, mock_manager):
        """Test adding exclusions by index."""
        with patch("builtins.print") as mock_print:
            exclusions_add_logic(mock_manager, "0,1", "test reason", True, False)

            mock_manager.add_by_index.assert_called_once()
            expected_output = {
                "action": "add",
                "added_count": 1,
                "added_ids": ["test-id-1"],
                "reason": "test reason",
            }
            mock_print.assert_called_once_with(json.dumps(expected_output))

    def test_exclusions_add_logic_by_wildcard(self, mock_manager):
        """Test adding exclusions by wildcard pattern."""
        with patch("builtins.print") as mock_print:
            exclusions_add_logic(mock_manager, "test*", "test reason", True, False)

            mock_manager.add_by_wildcard.assert_called_once()
            expected_output = {
                "action": "add",
                "added_count": 1,
                "added_ids": ["test-id-2"],
                "reason": "test reason",
            }
            mock_print.assert_called_once_with(json.dumps(expected_output))

    def test_exclusions_add_logic_invalid_index(self, mock_manager):
        """Test adding exclusions with invalid index."""
        with (
            patch("builtins.print") as mock_print,
            pytest.raises(typer.Exit),
        ):
            exclusions_add_logic(mock_manager, "999", "test reason", True, False)

            expected_output = {"error": "Invalid server index: 999 (max: 1)"}
            mock_print.assert_called_once_with(json.dumps(expected_output))


class TestExclusionsRemoveLogic:
    """Test the internal exclusions remove logic (adapted for new structure)."""

    @pytest.fixture
    def mock_manager(self, supported_protocols):
        """Mock ExclusionManager with server cache."""
        manager = MagicMock()
        manager._servers_cache = {
            "servers": [{"type": "vless", "tag": "test1"}, {"type": "vmess", "tag": "test2"}],
            "supported_protocols": supported_protocols,
            "supported_servers": [{"type": "vless"}, {"type": "vmess"}],
        }
        manager.remove_by_index.return_value = ["test-id-1"]
        manager.remove.return_value = True
        manager.has_servers_cache.return_value = True
        return manager

    def test_exclusions_remove_logic_by_index(self, mock_manager):
        """Test removing exclusions by index."""
        with patch("builtins.print") as mock_print:
            exclusions_remove_logic(mock_manager, "0,1", True, False)

            mock_manager.remove_by_index.assert_called_once()
            expected_output = {
                "action": "remove",
                "removed_count": 1,
                "removed_ids": ["test-id-1"],
            }
            mock_print.assert_called_once_with(json.dumps(expected_output))

    def test_exclusions_remove_logic_by_id(self, mock_manager):
        """Test removing exclusions by server ID."""
        with patch("builtins.print") as mock_print:
            exclusions_remove_logic(mock_manager, "test-id-123", True, False)

            mock_manager.remove.assert_called_once_with("test-id-123")
            expected_output = {
                "action": "remove",
                "removed_count": 1,
                "removed_ids": ["test-id-123"],
            }
            mock_print.assert_called_once_with(json.dumps(expected_output))


class TestExclusionsListLogic:
    """Test the internal exclusions list logic (adapted for new structure)."""

    @pytest.fixture
    def mock_manager(self):
        """Mock ExclusionManager for testing."""
        manager = MagicMock()
        manager.list_all.return_value = []
        return manager

    def test_exclusions_list_logic_empty_json(self, mock_manager):
        """Test exclusions list logic with empty exclusions in JSON format."""
        with patch("builtins.print") as mock_print:
            exclusions_list_logic(mock_manager, True)

            expected_output = {"total": 0, "exclusions": []}
            mock_print.assert_called_once_with(json.dumps(expected_output, indent=2))

    def test_exclusions_list_logic_empty_table(self, mock_manager):
        """Test exclusions list logic with empty exclusions in table format."""
        with patch("sboxmgr.cli.commands.subscription.exclusions_logic.console.print") as mock_console:
            exclusions_list_logic(mock_manager, False)

            mock_console.assert_called_once_with("[dim]📝 No exclusions found.[/dim]")


class TestExclusionsClearLogic:
    """Test the internal exclusions clear logic (adapted for new structure)."""

    @pytest.fixture
    def mock_manager(self):
        """Mock ExclusionManager for testing."""
        manager = MagicMock()
        manager.list_all.return_value = []
        manager.clear.return_value = 0
        return manager

    def test_exclusions_clear_logic_confirmed(self, mock_manager):
        """Test exclusions clear logic with confirmation."""
        mock_manager.clear.return_value = 5
        mock_manager.list_all.return_value = [{"id": "test1"}, {"id": "test2"}]

        with (
            patch("rich.prompt.Confirm.ask", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            exclusions_clear_logic(mock_manager, True, False)

            mock_manager.clear.assert_called_once()
            expected_output = {"action": "clear", "removed_count": 5}
            mock_print.assert_called_once_with(json.dumps(expected_output))

    def test_exclusions_clear_logic_cancelled(self, mock_manager):
        """Test exclusions clear logic with cancellation."""
        mock_manager.list_all.return_value = [{"id": "test1"}]

        with (
            patch("rich.prompt.Confirm.ask", return_value=False),
            patch("sboxmgr.cli.commands.subscription.exclusions_logic.console.print") as mock_console,
        ):
            exclusions_clear_logic(mock_manager, False, False)

            mock_manager.clear.assert_not_called()
            mock_console.assert_called_once()
            call_args = mock_console.call_args[0][0]
            assert "[yellow]" in call_args


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
