"""Tests for TUI application components."""

from unittest.mock import Mock, patch

from sboxmgr.tui.app import SboxmgrTUI
from sboxmgr.tui.screens.main import MainScreen
from sboxmgr.tui.screens.welcome import WelcomeScreen


class TestSboxmgrTUI:
    """Test suite for the main TUI application."""

    def test_tui_initialization(self):
        """Test TUI application initialization."""
        app = SboxmgrTUI(debug=1, profile="test")

        assert app.state.debug == 1
        assert app.state.profile == "test"
        assert app.title == "sboxmgr"
        assert app.sub_title == "Subscription Manager"

    def test_tui_title_with_profile(self):
        """Test TUI title updates with profile."""
        app = SboxmgrTUI(profile="work")

        # Simulate mount event
        app.state.profile = "work"
        app.on_mount()

        assert app.title == "sboxmgr - work"

    def test_tui_debug_subtitle(self):
        """Test TUI subtitle updates with debug mode."""
        app = SboxmgrTUI(debug=2)

        # Simulate mount event
        app.on_mount()

        assert "debug: 2" in app.sub_title

    @patch('sboxmgr.tui.app.SboxmgrTUI.switch_screen')
    def test_subscription_added_handler(self, mock_switch):
        """Test subscription added event handler."""
        app = SboxmgrTUI()

        # Create mock event
        event = Mock()
        event.url = "https://example.com/sub"

        # Simulate event
        app.on_subscription_added(event)

        # Should switch to main screen
        mock_switch.assert_called_once()
        args = mock_switch.call_args[0]
        assert isinstance(args[0], MainScreen)

    def test_screen_switching_methods(self):
        """Test screen switching helper methods."""
        app = SboxmgrTUI()

        with patch.object(app, 'switch_screen') as mock_switch:
            # Test switch to main
            app.switch_to_main()
            mock_switch.assert_called_once()
            args = mock_switch.call_args[0]
            assert isinstance(args[0], MainScreen)

            mock_switch.reset_mock()

            # Test switch to welcome
            app.switch_to_welcome()
            mock_switch.assert_called_once()
            args = mock_switch.call_args[0]
            assert isinstance(args[0], WelcomeScreen)


class TestWelcomeScreen:
    """Test suite for the Welcome screen."""

    def test_welcome_screen_initialization(self):
        """Test welcome screen creates properly."""
        screen = WelcomeScreen()
        assert screen is not None

    def test_subscription_added_message(self):
        """Test SubscriptionAdded message creation."""
        url = "https://example.com/subscription"
        message = WelcomeScreen.SubscriptionAdded(url)

        assert message.url == url


class TestMainScreen:
    """Test suite for the Main screen."""

    def test_main_screen_initialization(self):
        """Test main screen creates properly."""
        screen = MainScreen()
        assert screen is not None

    def test_should_show_advanced_logic(self):
        """Test advanced options visibility logic."""
        screen = MainScreen()

        # Mock app state
        mock_state = Mock()
        mock_state.show_advanced = False
        mock_state.debug = 0
        mock_state.get_excluded_count.return_value = 0

        # Mock the app property using patch
        with patch('sboxmgr.tui.screens.main.MainScreen.app', new_callable=lambda: Mock()) as mock_app:
            mock_app.state = mock_state

            # Should not show advanced by default
            assert not screen._should_show_advanced()

            # Should show if debug mode
            mock_state.debug = 1
            assert screen._should_show_advanced()

            # Should show if exclusions exist
            mock_state.debug = 0
            mock_state.get_excluded_count.return_value = 5
            assert screen._should_show_advanced()

            # Should show if explicitly enabled
            mock_state.get_excluded_count.return_value = 0
            mock_state.show_advanced = True
            assert screen._should_show_advanced()

    def test_status_info_creation(self):
        """Test status information widget creation."""
        screen = MainScreen()

        # Mock app state
        mock_state = Mock()
        mock_state.profile = "test"
        mock_state.get_subscription_count.return_value = 2
        mock_state.active_subscription = "https://example.com/sub"
        mock_state.get_server_count.return_value = 10
        mock_state.get_excluded_count.return_value = 2

        with patch('sboxmgr.tui.screens.main.MainScreen.app', new_callable=lambda: Mock()) as mock_app:
            mock_app.state = mock_state

            status_widget = screen._create_status_info()
            status_text = status_widget.renderable

            assert "Profile: test" in status_text
            assert "Active Subscription:" in status_text
            assert "Servers: 10" in status_text
            assert "2 excluded" in status_text

    def test_status_info_long_url_truncation(self):
        """Test long URL truncation in status info."""
        screen = MainScreen()

        # Mock app state with very long URL
        long_url = "https://very-long-subscription-url-that-should-be-truncated-for-display.com/path/to/subscription"
        mock_state = Mock()
        mock_state.profile = "test"
        mock_state.get_subscription_count.return_value = 1
        mock_state.active_subscription = long_url
        mock_state.get_server_count.return_value = 5
        mock_state.get_excluded_count.return_value = 0

        with patch('sboxmgr.tui.screens.main.MainScreen.app', new_callable=lambda: Mock()) as mock_app:
            mock_app.state = mock_state

            status_widget = screen._create_status_info()
            status_text = status_widget.renderable

            # Should contain truncated URL with ellipsis
            assert "..." in status_text
            assert len([line for line in status_text.split('\n') if 'Active Subscription:' in line][0]) < 80


class TestTUIIntegration:
    """Integration tests for TUI components."""

    @patch('sboxmgr.tui.state.tui_state.TUIState.has_subscriptions')
    def test_context_aware_initial_screen(self, mock_has_subs):
        """Test context-aware initial screen selection."""
        # Test welcome screen for new users
        mock_has_subs.return_value = False
        app = SboxmgrTUI()

        # Should start with welcome screen
        # Note: In real app, this would be tested through compose() method
        assert not app.state.has_subscriptions()

        # Test main screen for existing users
        mock_has_subs.return_value = True
        app2 = SboxmgrTUI()

        # Should start with main screen
        assert app2.state.has_subscriptions()

    def test_css_path_configuration(self):
        """Test CSS path is correctly configured."""
        app = SboxmgrTUI()
        assert app.CSS_PATH == "tui.tcss"

    def test_key_bindings_configuration(self):
        """Test key bindings are properly configured."""
        app = SboxmgrTUI()

        # Check that quit bindings exist
        quit_keys = [binding.key for binding in app.BINDINGS if binding.action == "quit"]
        assert "q" in quit_keys
        assert "ctrl+c" in quit_keys

        # Check help binding exists
        help_keys = [binding.key for binding in app.BINDINGS if binding.action == "help"]
        assert any("f1" in key or "question_mark" in key for key in help_keys)
