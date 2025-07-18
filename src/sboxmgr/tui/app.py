"""Main TUI application for sboxmgr.

This module provides the main Textual application class that orchestrates
the entire TUI experience, including screen management and state handling.
"""

from typing import Optional

from textual import on
from textual.app import App
from textual.binding import Binding

from sboxmgr.tui.screens.main import MainScreen
from sboxmgr.tui.screens.welcome import WelcomeScreen
from sboxmgr.tui.state.tui_state import TUIState


class SboxmgrTUI(App):
    """Main TUI application for sboxmgr.

    This is the entry point for the Text User Interface mode of sboxmgr.
    It manages the overall application state and screen transitions based
    on the context-aware UI principles.

    Attributes:
        CSS_PATH: Path to the CSS file for styling
        TITLE: Application title
        SUB_TITLE: Application subtitle
        BINDINGS: Key bindings for the application
        state: The global TUI state

    """

    CSS_PATH = "tui.tcss"
    TITLE = "sboxmgr"
    SUB_TITLE = "Subscription Manager"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("escape", "go_back", "Back", priority=True),
        Binding("f1,question_mark", "help", "Help"),
        Binding("f10", "debug_info", "Debug Info", show=False),
    ]

    def __init__(self, debug: int = 0, profile: Optional[str] = None, **kwargs):
        """Initialize the TUI application.

        Args:
            debug: Debug level (0-3)
            profile: Profile name to use
            **kwargs: Additional arguments passed to App

        """
        super().__init__(**kwargs)
        self.state = TUIState(debug=debug, profile=profile)

    def compose(self):
        """Compose the main application layout.

        Returns:
            Empty list - we'll install the initial screen in on_mount

        """
        # Empty compose - we'll install the initial screen in on_mount
        return []

    def on_mount(self) -> None:
        """Handle application mount event."""
        # Update window title with profile info
        if self.state.profile:
            self.title = f"sboxmgr - {self.state.profile}"

        # Set debug mode if requested
        if self.state.debug > 0:
            self.sub_title = f"Subscription Manager (debug: {self.state.debug})"

        # Install initial screen based on context
        if not self.state.has_subscriptions():
            self.push_screen(WelcomeScreen(id="welcome"))
        else:
            self.push_screen(MainScreen(id="main"))

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen in Phase 3
        self.bell()

    def action_debug_info(self) -> None:
        """Show debug information."""
        if self.state.debug > 0:
            # TODO: Implement debug info modal in Phase 3
            self.bell()

    def action_go_back(self) -> None:
        """Go back to previous screen or main menu."""
        # If we're not on the main screen or welcome screen, go back
        current_screen = self.screen
        if current_screen.id not in ["main", "welcome"]:
            self.pop_screen()
        else:
            # On main/welcome screen, show notification
            self.notify("Press 'q' to quit", severity="information")

    @on(WelcomeScreen.SubscriptionAdded)
    def on_subscription_added(self, event: WelcomeScreen.SubscriptionAdded) -> None:
        """Handle subscription addition from welcome screen.

        Args:
            event: The subscription added event

        """
        # Transition from welcome to main screen
        self.switch_screen(MainScreen(id="main"))

    def switch_to_main(self) -> None:
        """Switch to main screen.

        This method provides a clean way to transition to the main screen
        from any other screen in the application.
        """
        self.switch_screen(MainScreen(id="main"))

    def switch_to_welcome(self) -> None:
        """Switch to welcome screen.

        This method provides a clean way to transition to the welcome screen,
        typically used when all subscriptions are removed.
        """
        self.switch_screen(WelcomeScreen(id="welcome"))
