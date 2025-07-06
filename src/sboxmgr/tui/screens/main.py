"""Main screen with navigation menu.

This module implements the main screen that is shown to users
who have subscriptions configured. It provides the main navigation
menu with context-aware options.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from sboxmgr.tui.components.forms import ConfigGenerationForm


class MainScreen(Screen):
    """Main screen with navigation menu.

    This screen is displayed when the user has subscriptions configured.
    It provides the main navigation menu with context-aware options
    based on the current application state.

    The screen implements the context-aware UI principle by showing
    different options based on available subscriptions and user preferences.
    """

    CSS = """
    MainScreen {
        layout: vertical;
    }

    .main-container {
        layout: vertical;
        padding: 1;
        height: 1fr;
    }

    .status-bar {
        background: $surface;
        color: $text;
        padding: 0 1;
        height: 3;
        border: solid $primary;
    }

    .menu-container {
        layout: vertical;
        padding: 1;
        height: 1fr;
        align: center middle;
    }

    .menu-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .menu-buttons {
        layout: vertical;
        width: 40;
        height: auto;
    }

    .menu-buttons Button {
        margin: 0 0 1 0;
        width: 100%;
    }

    .advanced-section {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary;
    }

    .advanced-title {
        text-align: center;
        text-style: italic;
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the main screen layout.

        Returns:
            The composed result containing the main screen widgets
        """
        yield Header()

        with Vertical(classes="main-container"):
            # Status bar showing current state
            with Vertical(classes="status-bar"):
                yield self._create_status_info()

            # Main menu
            with Vertical(classes="menu-container"):
                yield Static("Main Menu", classes="menu-title")

                with Vertical(classes="menu-buttons"):
                    # Primary actions
                    yield Button(
                        "⚙️ Generate Config", id="generate_config", variant="primary"
                    )
                    yield Button("👁️ View Servers", id="view_servers", variant="default")
                    yield Button(
                        "🧷 Manage Subscriptions",
                        id="manage_subscriptions",
                        variant="default",
                    )

                    # Advanced section (conditionally shown)
                    if self._should_show_advanced():
                        with Vertical(classes="advanced-section"):
                            yield Static("Advanced", classes="advanced-title")
                            yield Button(
                                "🧠 Profile Settings",
                                id="profile_settings",
                                variant="default",
                            )
                            yield Button(
                                "🚫 Exclusion Manager",
                                id="exclusion_manager",
                                variant="default",
                            )

                    # Always show exit
                    yield Button("⏹ Exit", id="exit", variant="error")

        yield Footer()

    def _create_status_info(self) -> Static:
        """Create status information widget.

        Returns:
            Static widget with current status information
        """
        app_state = self.app.state

        # Build status text
        status_lines = []

        # Profile info
        profile = app_state.profile or "default"
        status_lines.append(f"Profile: {profile}")

        # Subscription info
        sub_count = app_state.get_subscription_count()
        if sub_count > 0:
            active_sub = app_state.active_subscription
            if active_sub:
                # Truncate long URLs
                display_url = active_sub
                if len(display_url) > 40:
                    display_url = display_url[:37] + "..."
                status_lines.append(f"Active Subscription: {display_url}")
            else:
                status_lines.append(f"Subscriptions: {sub_count}")

        # Server info
        server_count = app_state.get_server_count()
        excluded_count = app_state.get_excluded_count()
        if server_count > 0:
            server_info = f"Servers: {server_count}"
            if excluded_count > 0:
                server_info += f" ({excluded_count} excluded)"
            status_lines.append(server_info)

        # Add navigation hints
        if status_lines:
            status_lines.append("")  # Empty line
        status_lines.append("💡 Tip: Press 'Escape' to go back, 'q' to quit")

        return Static("\n".join(status_lines))

    def _should_show_advanced(self) -> bool:
        """Check if advanced options should be shown.

        Returns:
            True if advanced options should be displayed
        """
        app_state = self.app.state
        return (
            app_state.show_advanced
            or app_state.debug > 0
            or app_state.get_excluded_count() > 0
        )

    @on(Button.Pressed, "#generate_config")
    def on_generate_config_pressed(self) -> None:
        """Handle generate config button press."""
        self.app.push_screen(ConfigGenerationForm())

    @on(Button.Pressed, "#view_servers")
    def on_view_servers_pressed(self) -> None:
        """Handle view servers button press."""
        from sboxmgr.tui.screens.server_list import ServerListScreen

        self.app.push_screen(ServerListScreen())

    @on(Button.Pressed, "#manage_subscriptions")
    def on_manage_subscriptions_pressed(self) -> None:
        """Handle manage subscriptions button press."""
        from sboxmgr.tui.screens.subscription_manager import SubscriptionManagerScreen

        self.app.push_screen(SubscriptionManagerScreen())

    @on(Button.Pressed, "#profile_settings")
    def on_profile_settings_pressed(self) -> None:
        """Handle profile settings button press."""
        # TODO: Implement profile settings screen in Phase 4
        self.app.notify("Profile settings coming in Phase 4!", severity="info")

    @on(Button.Pressed, "#exclusion_manager")
    def on_exclusion_manager_pressed(self) -> None:
        """Handle exclusion manager button press."""
        # TODO: Implement exclusion manager screen in Phase 4
        self.app.notify("Exclusion manager coming in Phase 4!", severity="info")

    @on(Button.Pressed, "#exit")
    def on_exit_pressed(self) -> None:
        """Handle exit button press."""
        self.app.exit()

    def on_key(self, event) -> None:
        """Handle arrow key navigation for menu buttons."""
        # Собираем все кнопки меню
        buttons = [w for w in self.query(".menu-buttons Button")]
        if not buttons:
            return
        focused = self.focused
        current_index = None
        for i, btn in enumerate(buttons):
            if btn is focused:
                current_index = i
                break
        if event.key == "down":
            next_index = (current_index + 1) if current_index is not None else 0
            if next_index < len(buttons):
                buttons[next_index].focus()
        elif event.key == "up":
            prev_index = (
                (current_index - 1) if current_index is not None else len(buttons) - 1
            )
            if prev_index >= 0:
                buttons[prev_index].focus()
