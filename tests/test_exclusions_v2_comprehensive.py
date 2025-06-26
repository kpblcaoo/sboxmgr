"""
Comprehensive tests for exclusions_v2.py CLI commands.

Test coverage:
- Add exclusions by index, wildcard patterns
- Remove exclusions by index and ID
- View exclusions and list servers
- JSON output format for all operations
- Error handling for fetch failures and invalid data
- Interactive mode operations
- Helper function unit tests
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typer.testing import CliRunner
from rich.console import Console
from rich.table import Table
from click.exceptions import Exit

from sboxmgr.cli.commands.exclusions_v2 import (
    exclusions_v2,
    _handle_clear_operation,
    _fetch_and_validate_subscription,
    _cache_server_data,
    _show_usage_help,
    _view_exclusions,
    _list_servers,
    _interactive_exclusions,
    _add_exclusions,
    _remove_exclusions,
    _get_server_id
)
from sboxmgr.core.exclusions.manager import ExclusionManager
from sboxmgr.cli.main import app

runner = CliRunner()


class TestExclusionsV2CLI:
    """Test suite for exclusions_v2 CLI command."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock ExclusionManager with test data."""
        manager = Mock(spec=ExclusionManager)
        manager.list_all.return_value = [
            {
                "id": "server123abc",
                "name": "Test Server 1",
                "reason": "Testing",
                "timestamp": "2024-01-01T10:00:00"
            }
        ]
        manager.list_servers.return_value = [
            (0, {"tag": "server1", "type": "vless", "server": "1.1.1.1", "server_port": 443}, False),
            (1, {"tag": "server2", "type": "vmess", "server": "2.2.2.2", "server_port": 80}, True)
        ]
        manager._servers_cache = {
            'servers': [
                {"tag": "server1", "type": "vless", "server": "1.1.1.1", "server_port": 443},
                {"tag": "server2", "type": "vmess", "server": "2.2.2.2", "server_port": 80}
            ],
            'supported_protocols': ['vless', 'vmess']
        }
        manager.clear.return_value = 5
        manager.add_by_index.return_value = ["id1", "id2"]
        manager.add_by_wildcard.return_value = ["id3"]
        manager.remove_by_index.return_value = ["id1"]
        manager.remove.return_value = True
        manager._get_server_id = Mock(return_value="server123")
        return manager

    @pytest.fixture
    def mock_json_data(self):
        """Mock subscription JSON data."""
        return {
            "servers": [
                {"tag": "server1", "type": "vless", "server": "1.1.1.1", "server_port": 443},
                {"tag": "server2", "type": "vmess", "server": "2.2.2.2", "server_port": 80}
            ]
        }

    def test_exclusions_v2_no_action_shows_help(self, mock_manager, mock_json_data):
        """Test that no action specified shows usage help."""
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data), \
             patch('sboxmgr.cli.commands.exclusions_v2._show_usage_help') as mock_help:
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, ["exclusions-v2", "--url", "http://test.com"])
            mock_help.assert_called_once()

    def test_exclusions_v2_add_by_indices(self, mock_manager, mock_json_data):
        """Test adding exclusions by server indices."""
        mock_manager._servers_cache = {'servers': mock_json_data['servers'], 'supported_protocols': ['vless', 'vmess']}
        mock_manager.add_by_index.return_value = ['server1_id', 'server2_id']
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", 
                "--add", "0,1", "--reason", "Test reason"
            ])
            
            assert result.exit_code == 0
            mock_manager.add_by_index.assert_called_once()

    def test_exclusions_v2_add_by_wildcard(self, mock_manager, mock_json_data):
        """Test adding exclusions by wildcard patterns."""
        mock_manager._servers_cache = {'servers': mock_json_data['servers'], 'supported_protocols': ['vless', 'vmess']}
        mock_manager.add_by_wildcard.return_value = ['server1_id', 'server2_id']
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", 
                "--add", "server-*,test-*", "--reason", "Wildcard test"
            ])
            
            assert result.exit_code == 0
            mock_manager.add_by_wildcard.assert_called_once()

    def test_exclusions_v2_remove_by_indices(self, mock_manager, mock_json_data):
        """Test removing exclusions by server indices."""
        mock_manager._servers_cache = {'servers': mock_json_data['servers'], 'supported_protocols': ['vless', 'vmess']}
        mock_manager.remove_by_index.return_value = ['server1_id', 'server2_id']
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", 
                "--remove", "0,1"
            ])
            
            assert result.exit_code == 0
            mock_manager.remove_by_index.assert_called_once()

    def test_exclusions_v2_remove_by_ids(self, mock_manager, mock_json_data):
        """Test removing exclusions by server IDs."""
        mock_manager._servers_cache = {'servers': mock_json_data['servers'], 'supported_protocols': ['vless', 'vmess']}
        mock_manager.remove.return_value = True
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", 
                "--remove", "server123abc"
            ])
            
            assert result.exit_code == 0
            mock_manager.remove.assert_called_once_with("server123abc")

    def test_exclusions_v2_view_command(self, mock_manager, mock_json_data):
        """Test view exclusions command."""
        mock_manager.list_all.return_value = []
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--view"
            ])
            
            assert result.exit_code == 0
            mock_manager.list_all.assert_called_once()

    def test_exclusions_v2_clear_command_confirmed(self, mock_manager, mock_json_data):
        """Test clear exclusions command with confirmation."""
        mock_manager.clear.return_value = 5
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data), \
             patch('rich.prompt.Confirm.ask', return_value=True):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--clear"
            ])
            
            assert result.exit_code == 0
            mock_manager.clear.assert_called_once()

    def test_exclusions_v2_clear_command_cancelled(self, mock_manager, mock_json_data):
        """Test clear exclusions command cancelled by user."""
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data), \
             patch('rich.prompt.Confirm.ask', return_value=False):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--clear"
            ])
            
            assert result.exit_code == 0
            mock_manager.clear.assert_not_called()

    def test_exclusions_v2_list_servers_command(self, mock_manager, mock_json_data):
        """Test list servers command."""
        mock_manager._servers_cache = {'servers': mock_json_data['servers'], 'supported_protocols': ['vless', 'vmess']}
        mock_manager.list_servers.return_value = []
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--list-servers"
            ])
            
            assert result.exit_code == 0
            mock_manager.list_servers.assert_called_once()

    def test_exclusions_v2_json_output_format(self, mock_manager, mock_json_data):
        """Test JSON output format for all commands."""
        mock_manager.list_all.return_value = []
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            # Test view with JSON
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--view", "--json"
            ])
            assert result.exit_code == 0
            # Should contain valid JSON
            try:
                json.loads(result.stdout)
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_exclusions_v2_fetch_failure(self, mock_manager):
        """Test handling of subscription fetch failures."""
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=None):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://invalid.com", "--list-servers"
            ])
            
            assert result.exit_code == 1

    def test_exclusions_v2_fetch_exception(self, mock_manager):
        """Test handling of subscription fetch exceptions."""
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', side_effect=Exception("Network error")):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://error.com", "--list-servers"
            ])
            
            assert result.exit_code == 1

    def test_exclusions_v2_cache_server_data_error(self, mock_manager, mock_json_data):
        """Test handling of server data caching errors."""
        mock_manager.set_servers_cache.side_effect = Exception("Invalid format")
        
        with patch('sboxmgr.cli.commands.exclusions_v2.ExclusionManager') as mock_class, \
             patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_json_data):
            
            mock_class.default.return_value = mock_manager
            result = runner.invoke(app, [
                "exclusions-v2", "--url", "http://test.com", "--list-servers"
            ])
            
            assert result.exit_code == 1


class TestExclusionsV2HelperFunctions:
    """Test suite for exclusions_v2 helper functions."""

    def test_handle_clear_operation_confirmed(self):
        """Test clear operation with user confirmation."""
        mock_manager = Mock()
        mock_manager.clear.return_value = 3
        
        with patch('rich.prompt.Confirm.ask', return_value=True), \
             patch('rich.console.Console.print') as mock_print:
            
            _handle_clear_operation(mock_manager, False)
            mock_manager.clear.assert_called_once()

    def test_handle_clear_operation_cancelled(self):
        """Test clear operation cancelled by user."""
        mock_manager = Mock()
        
        with patch('rich.prompt.Confirm.ask', return_value=False):
            _handle_clear_operation(mock_manager, False)
            mock_manager.clear.assert_not_called()

    def test_handle_clear_operation_json_output(self):
        """Test clear operation with JSON output."""
        mock_manager = Mock()
        mock_manager.clear.return_value = 5
        
        with patch('rich.prompt.Confirm.ask', return_value=True), \
             patch('builtins.print') as mock_print:
            
            _handle_clear_operation(mock_manager, True)
            mock_print.assert_called_once()
            # Verify JSON structure
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert data["action"] == "clear"
            assert data["removed_count"] == 5

    def test_fetch_and_validate_subscription_success(self):
        """Test successful subscription fetch and validation."""
        mock_data = {"servers": [{"tag": "test"}]}
        
        with patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=mock_data):
            result = _fetch_and_validate_subscription("http://test.com", False)
            assert result == mock_data

    def test_fetch_and_validate_subscription_none_result(self):
        """Test subscription fetch returning None."""
        with patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=None), \
             pytest.raises(Exit):
            
            _fetch_and_validate_subscription("http://test.com", False)

    def test_fetch_and_validate_subscription_exception(self):
        """Test subscription fetch raising exception."""
        with patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', side_effect=Exception("Error")), \
             pytest.raises(Exit):
            
            _fetch_and_validate_subscription("http://test.com", False)

    def test_fetch_and_validate_subscription_json_output(self):
        """Test subscription fetch with JSON error output."""
        with patch('sboxmgr.cli.commands.exclusions_v2.fetch_json', return_value=None), \
             patch('builtins.print') as mock_print, \
             pytest.raises(Exit):
            
            _fetch_and_validate_subscription("http://test.com", True)
            mock_print.assert_called_once()
            # Verify JSON error format
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert "error" in data
            assert "url" in data

    def test_cache_server_data_success(self):
        """Test successful server data caching."""
        mock_manager = Mock()
        mock_data = {"servers": []}
        
        _cache_server_data(mock_manager, mock_data, False)
        mock_manager.set_servers_cache.assert_called_once()

    def test_cache_server_data_exception(self):
        """Test server data caching with exception."""
        mock_manager = Mock()
        mock_manager.set_servers_cache.side_effect = Exception("Invalid format")
        
        with pytest.raises(Exit):
            _cache_server_data(mock_manager, {}, False)

    def test_cache_server_data_exception_json_output(self):
        """Test server data caching exception with JSON output."""
        mock_manager = Mock()
        mock_manager.set_servers_cache.side_effect = Exception("Invalid format")
        
        with patch('builtins.print') as mock_print, \
             pytest.raises(Exit):
            
            _cache_server_data(mock_manager, {}, True)
            mock_print.assert_called_once()
            # Verify JSON error format
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert "error" in data

    def test_show_usage_help(self):
        """Test usage help display."""
        with patch('rich.console.Console.print') as mock_print:
            _show_usage_help()
            assert mock_print.call_count >= 1

    def test_view_exclusions_empty_list(self):
        """Test viewing exclusions with empty list."""
        mock_manager = Mock()
        mock_manager.list_all.return_value = []
        
        with patch('rich.console.Console.print') as mock_print:
            _view_exclusions(mock_manager, False)
            mock_manager.list_all.assert_called_once()

    def test_view_exclusions_with_data(self):
        """Test viewing exclusions with data."""
        mock_manager = Mock()
        mock_manager.list_all.return_value = [
            {
                "id": "server123abc",
                "name": "Test Server",
                "reason": "Testing",
                "timestamp": "2024-01-01T10:00:00"
            }
        ]
        
        with patch('rich.console.Console.print') as mock_print:
            _view_exclusions(mock_manager, False)
            mock_manager.list_all.assert_called_once()

    def test_view_exclusions_json_output(self):
        """Test viewing exclusions with JSON output."""
        mock_manager = Mock()
        exclusions_data = [{"id": "test", "name": "Test"}]
        mock_manager.list_all.return_value = exclusions_data
        
        with patch('builtins.print') as mock_print:
            _view_exclusions(mock_manager, True)
            mock_print.assert_called_once()
            # Verify JSON structure
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert "total" in data
            assert "exclusions" in data
            assert data["total"] == len(exclusions_data)

    def test_list_servers_empty_list(self):
        """Test listing servers with empty list."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = []
        
        with patch('rich.console.Console.print') as mock_print:
            _list_servers(mock_manager, False, True)
            mock_manager.list_servers.assert_called_once_with(show_excluded=True)

    def test_list_servers_with_data(self):
        """Test listing servers with data."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [
            (0, {"tag": "server1", "type": "vless", "server": "1.1.1.1", "server_port": 443}, False),
            (1, {"tag": "server2", "type": "vmess", "server": "2.2.2.2", "server_port": 80}, True)
        ]
        mock_manager._get_server_id = Mock(return_value="server123")
        
        with patch('rich.console.Console.print') as mock_print:
            _list_servers(mock_manager, False, True)
            mock_manager.list_servers.assert_called_once()

    def test_list_servers_json_output(self):
        """Test listing servers with JSON output."""
        mock_manager = Mock()
        servers_data = [
            (0, {"tag": "server1", "type": "vless", "server": "1.1.1.1", "server_port": 443}, False)
        ]
        mock_manager.list_servers.return_value = servers_data
        mock_manager._get_server_id = Mock(return_value="server123")
        
        with patch('builtins.print') as mock_print:
            _list_servers(mock_manager, True, True)
            mock_print.assert_called_once()
            # Verify JSON structure
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert "total" in data
            assert "servers" in data

    def test_list_servers_arithmetic_operations(self):
        """Test arithmetic operations in server counting (critical business logic)."""
        mock_manager = Mock()
        # 3 servers: 2 available, 1 excluded
        servers_data = [
            (0, {"tag": "server1"}, False),  # available
            (1, {"tag": "server2"}, False),  # available  
            (2, {"tag": "server3"}, True),   # excluded
        ]
        mock_manager.list_servers.return_value = servers_data
        mock_manager._get_server_id = Mock(return_value="server123")
        
        with patch('rich.console.Console.print') as mock_print:
            _list_servers(mock_manager, False, True)
            
            # Verify arithmetic: available_count = len(servers_info) - excluded_count
            # Should be: 3 - 1 = 2 available, 1 excluded
            # This tests the critical business logic that mutation testing found
            print_calls = [str(call) for call in mock_print.call_args_list]
            summary_found = False
            for call_str in print_calls:
                if "Available: 2" in call_str and "Excluded: 1" in call_str:
                    summary_found = True
                    break
            assert summary_found, f"Expected summary with correct arithmetic not found in: {print_calls}"

    def test_add_exclusions_indices_only(self):
        """Test adding exclusions by indices only."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_index.return_value = ["id1", "id2"]
        
        with patch('rich.console.Console.print') as mock_print:
            _add_exclusions(mock_manager, "0,1", "Test reason", False)
            mock_manager.add_by_index.assert_called_once()

    def test_add_exclusions_patterns_only(self):
        """Test adding exclusions by patterns only."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_wildcard.return_value = ["id3"]
        
        with patch('rich.console.Console.print') as mock_print:
            _add_exclusions(mock_manager, "server-*,test-*", "Test reason", False)
            mock_manager.add_by_wildcard.assert_called_once()

    def test_add_exclusions_mixed_indices_and_patterns(self):
        """Test adding exclusions with mixed indices and patterns."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_index.return_value = ["id1"]
        mock_manager.add_by_wildcard.return_value = ["id2"]
        
        with patch('rich.console.Console.print') as mock_print:
            _add_exclusions(mock_manager, "0,server-*", "Mixed test", False)
            mock_manager.add_by_index.assert_called_once()
            mock_manager.add_by_wildcard.assert_called_once()

    def test_add_exclusions_no_cache_error(self):
        """Test adding exclusions without server cache."""
        mock_manager = Mock()
        mock_manager._servers_cache = None
        
        with patch('rich.console.Console.print') as mock_print:
            _add_exclusions(mock_manager, "0,1", "Test", False)
            # Should show error message about missing cache

    def test_add_exclusions_json_output(self):
        """Test adding exclusions with JSON output."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_index.return_value = ["id1", "id2"]
        
        with patch('builtins.print') as mock_print:
            _add_exclusions(mock_manager, "0,1", "Test reason", True)
            mock_print.assert_called_once()
            # Verify JSON structure
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert data["action"] == "add"
            assert data["added_count"] == 2
            assert data["reason"] == "Test reason"

    def test_add_exclusions_no_additions(self):
        """Test adding exclusions when nothing is added."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_index.return_value = []
        
        with patch('rich.console.Console.print') as mock_print:
            _add_exclusions(mock_manager, "0", "Test", False)
            # Should show warning about no additions

    def test_remove_exclusions_indices_only(self):
        """Test removing exclusions by indices only."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.remove_by_index.return_value = ["id1"]
        
        with patch('rich.console.Console.print') as mock_print:
            _remove_exclusions(mock_manager, "0,1", False)
            mock_manager.remove_by_index.assert_called_once()

    def test_remove_exclusions_ids_only(self):
        """Test removing exclusions by server IDs only."""
        mock_manager = Mock()
        mock_manager.remove.return_value = True
        
        with patch('rich.console.Console.print') as mock_print:
            _remove_exclusions(mock_manager, "server123abc", False)
            mock_manager.remove.assert_called_once_with("server123abc")

    def test_remove_exclusions_mixed_indices_and_ids(self):
        """Test removing exclusions with mixed indices and IDs."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.remove_by_index.return_value = ["id1"]
        mock_manager.remove.return_value = True
        
        with patch('rich.console.Console.print') as mock_print:
            _remove_exclusions(mock_manager, "0,server123abc", False)
            mock_manager.remove_by_index.assert_called_once()
            mock_manager.remove.assert_called_once()

    def test_remove_exclusions_no_cache_error(self):
        """Test removing exclusions without server cache."""
        mock_manager = Mock()
        mock_manager._servers_cache = None
        
        with patch('rich.console.Console.print') as mock_print:
            _remove_exclusions(mock_manager, "0,1", False)
            # Should show error about missing cache

    def test_remove_exclusions_json_output(self):
        """Test removing exclusions with JSON output."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.remove_by_index.return_value = ["id1"]
        
        with patch('builtins.print') as mock_print:
            _remove_exclusions(mock_manager, "0", True)
            mock_print.assert_called_once()
            # Verify JSON structure
            call_args = mock_print.call_args[0][0]
            data = json.loads(call_args)
            assert data["action"] == "remove"
            assert data["removed_count"] == 1

    def test_remove_exclusions_no_removals(self):
        """Test removing exclusions when nothing is removed."""
        mock_manager = Mock()
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.remove_by_index.return_value = []
        
        with patch('rich.console.Console.print') as mock_print:
            _remove_exclusions(mock_manager, "0", False)
            # Should show warning about no removals


class TestInteractiveExclusions:
    """Test suite for interactive exclusions functionality."""

    def test_interactive_exclusions_no_servers(self):
        """Test interactive mode with no servers."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = []
        
        with patch('rich.console.Console.print') as mock_print:
            _interactive_exclusions(mock_manager, False, "Test")
            mock_manager.list_servers.assert_called_once()

    def test_interactive_exclusions_quit_command(self):
        """Test interactive mode quit command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [
            (0, {"tag": "server1"}, False)
        ]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', return_value="quit"):
            
            _interactive_exclusions(mock_manager, False, "Test")

    def test_interactive_exclusions_view_command(self):
        """Test interactive mode view command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [
            (0, {"tag": "server1"}, False)
        ]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('sboxmgr.cli.commands.exclusions_v2._view_exclusions') as mock_view, \
             patch('rich.prompt.Prompt.ask', side_effect=["view", "quit"]):
            
            _interactive_exclusions(mock_manager, False, "Test")
            mock_view.assert_called_once()

    def test_interactive_exclusions_clear_command_confirmed(self):
        """Test interactive mode clear command with confirmation."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        mock_manager.clear.return_value = 3
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["clear", "quit"]), \
             patch('rich.prompt.Confirm.ask', return_value=True):
            
            _interactive_exclusions(mock_manager, False, "Test")
            mock_manager.clear.assert_called_once()

    def test_interactive_exclusions_add_command(self):
        """Test interactive mode add command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_index.return_value = ["id1"]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["add 0,1", "quit"]):
            
            _interactive_exclusions(mock_manager, False, "Test")
            mock_manager.add_by_index.assert_called_once()

    def test_interactive_exclusions_remove_command(self):
        """Test interactive mode remove command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.remove_by_index.return_value = ["id1"]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["remove 0", "quit"]):
            
            _interactive_exclusions(mock_manager, False, "Test")
            mock_manager.remove_by_index.assert_called_once()

    def test_interactive_exclusions_wildcard_command(self):
        """Test interactive mode wildcard command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        mock_manager._servers_cache = {
            'servers': [{"tag": "server1"}],
            'supported_protocols': ['vless']
        }
        mock_manager.add_by_wildcard.return_value = ["id1", "id2"]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["wildcard server-*", "quit"]):
            
            _interactive_exclusions(mock_manager, False, "Test")
            mock_manager.add_by_wildcard.assert_called_once()

    def test_interactive_exclusions_wildcard_no_cache(self):
        """Test interactive mode wildcard command without cache."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        mock_manager._servers_cache = None
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["wildcard server-*", "quit"]), \
             patch('rich.console.Console.print') as mock_print:
            
            _interactive_exclusions(mock_manager, False, "Test")
            # Should show error about missing cache

    def test_interactive_exclusions_unknown_command(self):
        """Test interactive mode with unknown command."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('rich.prompt.Prompt.ask', side_effect=["invalid", "quit"]), \
             patch('rich.console.Console.print') as mock_print:
            
            _interactive_exclusions(mock_manager, False, "Test")
            # Should show help message for unknown command

    def test_interactive_exclusions_syntax_warning_fix(self):
        """Test that interactive mode fixes the SyntaxWarning 'is' vs '=='."""
        mock_manager = Mock()
        mock_manager.list_servers.return_value = [(0, {"tag": "server1"}, False)]
        
        with patch('sboxmgr.cli.commands.exclusions_v2._list_servers'), \
             patch('sboxmgr.cli.commands.exclusions_v2._view_exclusions') as mock_view, \
             patch('rich.prompt.Prompt.ask', side_effect=["view", "quit"]):
            
            _interactive_exclusions(mock_manager, False, "Test")
            # This test ensures the line `elif command is "view":` is covered
            # and should be fixed to `elif command == "view":`
            mock_view.assert_called_once()


class TestGetServerIdHelper:
    """Test suite for _get_server_id helper function."""

    def test_get_server_id_function(self):
        """Test _get_server_id helper function."""
        server = {"tag": "test", "server": "1.1.1.1", "server_port": 443}
        
        with patch('sboxmgr.cli.commands.exclusions_v2.generate_server_id', return_value="server123") as mock_gen:
            result = _get_server_id(server)
            assert result == "server123"
            mock_gen.assert_called_once_with(server) 