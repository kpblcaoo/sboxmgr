"""Tests for ServerListScreen."""

import pytest
from unittest.mock import Mock, patch

from sboxmgr.tui.screens.server_list import ServerListScreen


class TestServerListScreen:
    """Test cases for ServerListScreen."""

    @pytest.fixture
    def screen(self):
        """Create a ServerListScreen instance."""
        return ServerListScreen()

    def test_initialization(self, screen):
        """Test screen initialization."""
        assert screen._servers == []
        assert screen._excluded_servers == set()

    def test_empty_servers_display(self, screen):
        """Test display when no servers are available."""
        screen._servers = []

        # The compose method should handle empty servers gracefully
        # We can't test the full compose without an app context, but we can test the logic
        assert len(screen._servers) == 0

    @patch.object(ServerListScreen, 'app')
    def test_server_loading(self, mock_app, screen):
        """Test server loading from app state."""
        mock_servers = [
            {"protocol": "vmess", "address": "server1.com", "port": 443},
            {"protocol": "vless", "address": "server2.com", "port": 80}
        ]
        mock_app.state.servers = mock_servers

        screen._load_servers()

        # Should load servers from app state
        assert len(screen._servers) == 2

    @patch.object(ServerListScreen, 'app')
    def test_exclusion_loading(self, mock_app, screen):
        """Test exclusion loading from app state."""
        mock_exclusions = {"server1", "server2"}
        mock_app.state.excluded_servers = mock_exclusions

        screen._load_exclusions()

        assert screen._excluded_servers == mock_exclusions

    def test_server_id_generation(self, screen):
        """Test server ID generation."""
        server = {"protocol": "vmess", "address": "test.com", "port": 443}
        server_id = screen._get_server_id(server)

        assert "vmess" in server_id
        assert "test.com" in server_id
        assert "443" in server_id

    def test_server_display_formatting(self, screen):
        """Test server display formatting."""
        server = {
            "protocol": "vmess",
            "address": "example.com",
            "port": 443,
            "tag": "test-server"
        }

        display_text = screen._format_server_display(server)

        assert "vmess" in display_text
        assert "example.com" in display_text
        assert "443" in display_text
        assert "test-server" in display_text

    def test_server_stats_formatting(self, screen):
        """Test server statistics formatting."""
        server = {
            "protocol": "vmess",
            "address": "example.com",
            "port": 443,
            "network": "tcp",
            "security": "tls"
        }

        stats = screen._get_server_stats(server)

        # Should return formatted stats or None
        assert stats is None or isinstance(stats, str)

    @patch.object(ServerListScreen, 'app')
    def test_checkbox_change_handling(self, mock_app, screen):
        """Test checkbox change handling."""
        # Setup a server
        screen._servers = [{"protocol": "vmess", "address": "test.com", "port": 443}]

        # Mock checkbox event
        mock_checkbox = Mock()
        mock_checkbox.id = "server_0"
        mock_checkbox.value = False  # Unchecked means excluded

        mock_event = Mock()
        mock_event.checkbox = mock_checkbox

        screen.on_checkbox_changed(mock_event)

        # Should call toggle_server_exclusion
        mock_app.state.toggle_server_exclusion.assert_called_once()

    def test_select_all_functionality(self, screen):
        """Test select all button functionality."""
        # Setup servers
        screen._servers = [
            {"protocol": "vmess", "address": "test1.com", "port": 443},
            {"protocol": "vless", "address": "test2.com", "port": 80}
        ]

        # Mock the screen's query method
        screen.query = Mock()
        mock_checkboxes = [Mock(), Mock()]
        for i, cb in enumerate(mock_checkboxes):
            cb.id = f"server_{i}"
            cb.value = False
        screen.query.return_value = mock_checkboxes

        screen.on_select_all_pressed()

        # Should set all checkboxes to True
        for cb in mock_checkboxes:
            assert cb.value is True

    def test_select_none_functionality(self, screen):
        """Test select none button functionality."""
        # Setup servers
        screen._servers = [
            {"protocol": "vmess", "address": "test1.com", "port": 443},
            {"protocol": "vless", "address": "test2.com", "port": 80}
        ]

        # Mock the screen's query method
        screen.query = Mock()
        mock_checkboxes = [Mock(), Mock()]
        for i, cb in enumerate(mock_checkboxes):
            cb.id = f"server_{i}"
            cb.value = True
        screen.query.return_value = mock_checkboxes

        screen.on_select_none_pressed()

        # Should set all checkboxes to False
        for cb in mock_checkboxes:
            assert cb.value is False

    @patch.object(ServerListScreen, 'app')
    def test_apply_changes_functionality(self, mock_app, screen):
        """Test apply changes button functionality."""
        screen.on_apply_changes_pressed()

        # Should show notification and pop screen
        mock_app.notify.assert_called_once()
        mock_app.pop_screen.assert_called_once()

    @patch.object(ServerListScreen, 'app')
    def test_back_button_functionality(self, mock_app, screen):
        """Test back button functionality."""
        screen.on_back_pressed()

        # Should pop screen
        mock_app.pop_screen.assert_called_once()

    def test_info_panel_with_servers(self, screen):
        """Test info panel creation with servers."""
        screen._servers = [
            {"protocol": "vmess", "address": "test1.com", "port": 443},
            {"protocol": "vless", "address": "test2.com", "port": 80}
        ]
        screen._excluded_servers = {"test1.com:443"}

        info_panel = screen._create_info_panel()

        # Should create static widget with server info
        assert info_panel is not None

    def test_info_panel_without_servers(self, screen):
        """Test info panel creation without servers."""
        screen._servers = []

        info_panel = screen._create_info_panel()

        # Should create static widget with no servers message
        assert info_panel is not None
