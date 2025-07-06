"""Subscription management screen.

This module implements the subscription management screen that allows
users to add, remove, and manage their subscription sources.
"""

from typing import List

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from sboxmgr.tui.components.forms import SubscriptionForm
from sboxmgr.tui.utils.formatting import format_subscription_info


class SubscriptionManagerScreen(Screen):
    """Subscription management screen.

    This screen displays all configured subscription sources and allows
    users to add new ones, remove existing ones, and view their status.

    The screen implements the context-aware UI principle by showing
    subscription-specific information and management options.
    """

    CSS = """
    SubscriptionManagerScreen {
        layout: vertical;
    }

    .subscription-container {
        layout: vertical;
        padding: 1;
        height: 1fr;
    }

    .subscription-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .subscription-info {
        background: $surface;
        color: $text;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }

    .subscription-list {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    .subscription-item {
        layout: horizontal;
        height: 4;
        padding: 1;
        margin-bottom: 1;
        border: solid $primary;
        background: $surface;
    }

    .subscription-item:hover {
        background: $primary-darken-3;
    }

    .subscription-item.active {
        border: solid $accent;
        background: $accent-darken-3;
    }

    .subscription-details {
        width: 1fr;
        height: 4;
    }

    .subscription-url {
        color: $text;
        text-style: bold;
    }

    .subscription-type {
        color: $accent;
        text-style: italic;
    }

    .subscription-tags {
        color: $text-muted;
    }

    .subscription-status {
        color: $success;
    }

    .subscription-status.error {
        color: $error;
    }

    .subscription-actions {
        layout: vertical;
        width: 20;
        height: 4;
    }

    .subscription-actions Button {
        width: 100%;
        margin-bottom: 0;
    }

    .action-buttons {
        layout: horizontal;
        height: 3;
        padding: 1;
        background: $surface;
        border-top: solid $primary;
    }

    .action-buttons Button {
        margin: 0 1;
    }

    .empty-state {
        align: center middle;
        height: 1fr;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, **kwargs):
        """Initialize the subscription manager screen.

        Args:
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self._subscriptions: List = []
        self._active_subscription: str = ""

    def compose(self) -> ComposeResult:
        """Compose the subscription manager screen layout.

        Returns:
            The composed result containing the subscription manager widgets
        """
        yield Header()

        with Vertical(classes="subscription-container"):
            yield Static("Subscription Management", classes="subscription-title")

            # Info panel
            with Vertical(classes="subscription-info"):
                yield self._create_info_panel()

            # Subscription list or empty state
            if self._subscriptions:
                with VerticalScroll(classes="subscription-list"):
                    yield from self._create_subscription_items()
            else:
                with Vertical(classes="empty-state"):
                    yield Static(
                        "No subscriptions configured.\nAdd your first subscription to get started."
                    )

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button(
                    "Add Subscription", id="add_subscription", variant="primary"
                )
                yield Button("Refresh All", id="refresh_all", variant="default")
                yield Button("Back", id="back", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount event."""
        self._load_subscriptions()

    def _create_info_panel(self) -> Static:
        """Create the information panel.

        Returns:
            Static widget with subscription statistics
        """
        if not self._subscriptions:
            return Static("No subscriptions configured")

        total_subs = len(self._subscriptions)
        active_sub = self._active_subscription

        info_lines = [f"Total Subscriptions: {total_subs}"]

        if active_sub:
            # Truncate long URLs for display
            display_url = active_sub
            if len(display_url) > 50:
                display_url = display_url[:47] + "..."
            info_lines.append(f"Active: {display_url}")

        return Static("\n".join(info_lines))

    def _create_subscription_items(self) -> List:
        """Create subscription item widgets.

        Returns:
            List of subscription item widgets
        """
        items = []

        for i, subscription in enumerate(self._subscriptions):
            sub_url = self._get_subscription_url(subscription)
            is_active = sub_url == self._active_subscription

            # Create subscription item container
            item_classes = "subscription-item"
            if is_active:
                item_classes += " active"

            with Horizontal(classes=item_classes):
                # Subscription details
                details = self._format_subscription_display(subscription)
                details_widget = Static(details, classes="subscription-details")
                items.append(details_widget)

                # Action buttons
                with Vertical(classes="subscription-actions"):
                    if not is_active:
                        activate_btn = Button(
                            "Activate", id=f"activate_{i}", variant="primary"
                        )
                        items.append(activate_btn)

                    remove_btn = Button("Remove", id=f"remove_{i}", variant="error")
                    items.append(remove_btn)

        return items

    def _load_subscriptions(self) -> None:
        """Load subscriptions from the application state."""
        try:
            app_state = self.app.state
            if hasattr(app_state, "get_subscriptions"):
                self._subscriptions = app_state.get_subscriptions() or []
            else:
                self._subscriptions = []

            if hasattr(app_state, "active_subscription"):
                self._active_subscription = app_state.active_subscription or ""
            else:
                self._active_subscription = ""
        except Exception:
            self._subscriptions = []
            self._active_subscription = ""

    def _get_subscription_url(self, subscription) -> str:
        """Get URL from subscription object.

        Args:
            subscription: Subscription object

        Returns:
            Subscription URL
        """
        if hasattr(subscription, "url"):
            return subscription.url
        elif isinstance(subscription, str):
            return subscription
        else:
            return str(subscription)

    def _format_subscription_display(self, subscription) -> str:
        """Format subscription information for display.

        Args:
            subscription: Subscription object

        Returns:
            Formatted subscription information string
        """
        try:
            return format_subscription_info(subscription)
        except Exception:
            # Fallback formatting
            url = self._get_subscription_url(subscription)

            # Truncate long URLs
            if len(url) > 60:
                display_url = url[:57] + "..."
            else:
                display_url = url

            # Try to get type and tags
            sub_type = getattr(subscription, "source_type", "unknown")
            tags = getattr(subscription, "tags", [])

            lines = [f"URL: {display_url}"]
            lines.append(f"Type: {sub_type}")

            if tags:
                tag_str = ", ".join(tags[:3])  # Show max 3 tags
                if len(tags) > 3:
                    tag_str += f" (+{len(tags) - 3} more)"
                lines.append(f"Tags: {tag_str}")

            return "\n".join(lines)

    @on(Button.Pressed, "#add_subscription")
    def on_add_subscription_pressed(self) -> None:
        """Handle add subscription button press."""
        self.app.push_screen(SubscriptionForm(), self._handle_subscription_result)

    @on(Button.Pressed, "#refresh_all")
    def on_refresh_all_pressed(self) -> None:
        """Handle refresh all button press."""
        try:
            app_state = self.app.state
            if hasattr(app_state, "refresh_subscriptions"):
                app_state.refresh_subscriptions()
                self.app.notify("Refreshed all subscriptions", severity="success")
            else:
                self.app.notify("Refresh not available", severity="warning")
        except Exception as e:
            self.app.notify(
                f"Failed to refresh subscriptions: {str(e)}", severity="error"
            )

    @on(Button.Pressed, "#back")
    def on_back_pressed(self) -> None:
        """Handle back button press."""
        self.app.pop_screen()

    def _handle_subscription_result(self, result: bool | str) -> None:
        """Handle the result from the subscription form.

        Args:
            result: True if subscription was added successfully,
                   False if cancelled, or error message string
        """
        if result is True:
            # Reload subscriptions and refresh display
            self._load_subscriptions()
            self.refresh()
            self.app.notify("Subscription added successfully", severity="success")
        elif isinstance(result, str):
            # Handle error case
            self.app.notify(f"Error adding subscription: {result}", severity="error")
        # If result is False, user cancelled - do nothing

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events for dynamic buttons.

        Args:
            event: The button pressed event
        """
        button_id = event.button.id
        if not button_id:
            return

        if button_id.startswith("activate_"):
            self._handle_activate_subscription(button_id)
        elif button_id.startswith("remove_"):
            self._handle_remove_subscription(button_id)

    def _handle_activate_subscription(self, button_id: str) -> None:
        """Handle subscription activation.

        Args:
            button_id: Button ID containing subscription index
        """
        try:
            index = int(button_id.replace("activate_", ""))
            if 0 <= index < len(self._subscriptions):
                subscription = self._subscriptions[index]
                url = self._get_subscription_url(subscription)

                # Update application state
                app_state = self.app.state
                if hasattr(app_state, "set_active_subscription"):
                    app_state.set_active_subscription(url)
                    self._active_subscription = url

                    # Refresh display
                    self.refresh()
                    self.app.notify("Subscription activated", severity="success")
                else:
                    self.app.notify("Activation not available", severity="warning")
        except (ValueError, IndexError) as e:
            self.app.notify(
                f"Failed to activate subscription: {str(e)}", severity="error"
            )

    def _handle_remove_subscription(self, button_id: str) -> None:
        """Handle subscription removal.

        Args:
            button_id: Button ID containing subscription index
        """
        try:
            index = int(button_id.replace("remove_", ""))
            if 0 <= index < len(self._subscriptions):
                subscription = self._subscriptions[index]
                url = self._get_subscription_url(subscription)

                # Update application state
                app_state = self.app.state
                if hasattr(app_state, "remove_subscription"):
                    success = app_state.remove_subscription(url)
                    if success:
                        # Reload subscriptions and refresh display
                        self._load_subscriptions()
                        self.refresh()
                        self.app.notify("Subscription removed", severity="success")
                    else:
                        self.app.notify(
                            "Failed to remove subscription", severity="error"
                        )
                else:
                    self.app.notify("Removal not available", severity="warning")
        except (ValueError, IndexError) as e:
            self.app.notify(
                f"Failed to remove subscription: {str(e)}", severity="error"
            )
