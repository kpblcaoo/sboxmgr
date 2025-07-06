"""Welcome screen for first-time users.

This module implements the welcome screen that is shown to users
who don't have any subscriptions configured yet.
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Static

from sboxmgr.tui.components.forms import SubscriptionForm


class WelcomeScreen(Screen):
    """Welcome screen for first-time users.

    This screen is displayed when the user has no subscriptions configured.
    It provides a friendly introduction and guides the user to add their
    first subscription.

    The screen implements the context-aware UI principle by only showing
    relevant actions for new users.
    """

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    .welcome-container {
        width: 60;
        height: auto;
        border: thick $primary;
        padding: 2;
        margin: 1;
    }

    .welcome-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .welcome-description {
        text-align: center;
        margin-bottom: 2;
    }

    .welcome-buttons {
        align: center middle;
        height: auto;
    }

    .welcome-buttons Button {
        margin: 0 1;
    }
    """

    class SubscriptionAdded(Message):
        """Message sent when a subscription is successfully added."""

        def __init__(self, url: str) -> None:
            """Initialize the message.

            Args:
                url: The URL of the added subscription
            """
            super().__init__()
            self.url = url

    def compose(self) -> ComposeResult:
        """Compose the welcome screen layout.

        Returns:
            The composed result containing the welcome screen widgets
        """
        with Center():
            with Middle():
                with Vertical(classes="welcome-container"):
                    yield Static("👋 Welcome to sboxmgr!", classes="welcome-title")
                    yield Static(
                        "This tool helps you generate secure, reliable\n"
                        "configs for VPN proxies (like sing-box).\n\n"
                        "Let's start by adding your first subscription:",
                        classes="welcome-description",
                    )
                    with Center(classes="welcome-buttons"):
                        yield Button(
                            "Add Subscription", id="add_subscription", variant="primary"
                        )
                        yield Button("Exit", id="exit", variant="default")

    @on(Button.Pressed, "#add_subscription")
    def on_add_subscription_pressed(self) -> None:
        """Handle add subscription button press."""
        # Push the subscription form screen
        self.app.push_screen(SubscriptionForm(), self._handle_subscription_result)

    @on(Button.Pressed, "#exit")
    def on_exit_pressed(self) -> None:
        """Handle exit button press."""
        self.app.exit()

    def _handle_subscription_result(self, result: bool | str) -> None:
        """Handle the result from the subscription form.

        Args:
            result: True if subscription was added successfully,
                   False if cancelled, or error message string
        """
        if result is True:
            # Get the app state to check if we now have subscriptions
            app_state = self.app.state
            if app_state.has_subscriptions():
                # Send message that subscription was added
                active_url = app_state.active_subscription or "unknown"
                self.post_message(self.SubscriptionAdded(active_url))
        elif isinstance(result, str):
            # Handle error case - show notification
            self.app.notify(f"Error adding subscription: {result}", severity="error")
        # If result is False, user cancelled - do nothing
