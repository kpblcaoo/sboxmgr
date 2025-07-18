"""Subscription management screen.

This module implements the subscription management screen that allows
users to add, remove, and manage their subscription sources.
"""

from sboxmgr.tui.components.forms import SubscriptionForm
from sboxmgr.tui.utils.formatting import format_subscription_info
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static


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
        min-height: 20;
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
        min-height: 10;
        max-height: 15;
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
        height: 5;
        min-height: 5;
        padding: 1;
        background: $surface;
        border-top: solid $primary;
        align: center middle;
        dock: bottom;
    }

    .action-buttons Button {
        margin: 0 1;
        min-width: 15;
    }

    .action-buttons Button#back {
        background: $surface-lighten-2;
        border: solid $primary;
    }

    .action-buttons Button#back:hover {
        background: $primary-darken-3;
        color: $text;
    }

    .action-buttons Button#add_subscription {
        background: $success;
        color: $text;
        border: solid $success-darken-2;
    }

    .action-buttons Button#add_subscription:hover {
        background: $success-darken-2;
        color: $text;
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
        import logging

        logger = logging.getLogger("tui_debug")
        logger.debug("[DEBUG] SubscriptionManagerScreen.__init__ called")

        super().__init__(**kwargs)
        self._subscriptions: list = []
        self._active_subscription: str = ""

        logger.debug("[DEBUG] SubscriptionManagerScreen.__init__ completed")

    def compose(self) -> ComposeResult:
        """Compose the subscription manager screen layout.

        Returns:
            The composed result containing the subscription manager widgets
        """
        import logging

        logger = logging.getLogger("tui_debug")
        logger.debug("[DEBUG] SubscriptionManagerScreen.compose called")

        try:
            yield Header()

            with Vertical(classes="subscription-container"):
                yield Static("Subscription Management", classes="subscription-title")

                # Info panel
                with Vertical(classes="subscription-info"):
                    yield self._create_info_panel()

                # Subscription table
                with Vertical(classes="subscription-list"):
                    yield DataTable(id="subscription-table")

                # Action buttons
                with Horizontal(classes="action-buttons"):
                    logger.debug("[DEBUG] Creating action buttons")
                    add_button = Button(
                        "➕ Add New Subscription",
                        id="add_subscription",
                        variant="primary",
                    )
                    refresh_button = Button(
                        "🔄 Refresh All", id="refresh_all", variant="default"
                    )
                    back_button = Button("← Back", id="back", variant="default")

                    logger.debug(
                        f"[DEBUG] Created buttons: add={add_button}, refresh={refresh_button}, back={back_button}"
                    )

                    yield add_button
                    yield refresh_button
                    yield back_button

                    logger.debug("[DEBUG] Action buttons yielded")

            yield Footer()
            logger.debug("[DEBUG] SubscriptionManagerScreen.compose completed")
        except Exception as e:
            logger.error(f"[ERROR] Exception in compose: {e}")
            import traceback

            traceback.print_exc()
            # Fallback to basic layout
            yield Header()
            yield Static(
                "Error loading subscription manager", classes="subscription-title"
            )
            yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        import logging

        logger = logging.getLogger("tui_debug")
        logger.debug("[DEBUG] SubscriptionManagerScreen.on_mount called")
        try:
            self.load_subscriptions()
            logger.debug("[DEBUG] load_subscriptions completed")
        except Exception as e:
            logger.error(f"[ERROR] Exception in on_mount: {e}")
            import traceback

            traceback.print_exc()

    def load_subscriptions(self) -> None:
        """Load subscriptions from state."""
        import logging

        logger = logging.getLogger("tui_debug")
        logger.debug("[DEBUG] load_subscriptions called")

        try:
            table = self.query_one("#subscription-table", DataTable)
            table.clear()

            # Add columns
            table.add_columns("№", "URL", "Status", "Type", "Actions")

            # Load from app state (which now uses profiles)
            subscriptions = self.app.state.subscriptions
            logger.debug(f"[DEBUG] Found {len(subscriptions)} subscriptions")
        except Exception as e:
            logger.error(f"[ERROR] Exception in load_subscriptions: {e}")
            import traceback

            traceback.print_exc()
            return

        for i, subscription in enumerate(subscriptions):
            # Get subscription config from profile if available
            sub_config = None
            if self.app.state.active_config:
                subscription_urls = self.app.state.active_config.metadata.get(
                    "subscription_urls", {}
                )
                for sub_id, url in subscription_urls.items():
                    if url == subscription.url:
                        # Find corresponding config
                        for config in self.app.state.active_config.subscriptions:
                            if config.id == sub_id:
                                sub_config = config
                                break
                        break

            # Determine status
            enabled = sub_config.enabled if sub_config else True
            status = "✅ Enabled" if enabled else "❌ Disabled"

            # Truncate URL for display
            display_url = (
                subscription.url[:50] + "..."
                if len(subscription.url) > 50
                else subscription.url
            )

            # Add row with action buttons
            table.add_row(
                str(i + 1),
                display_url,
                status,
                subscription.source_type or "url",
                "[Remove] [Toggle]",
                key=str(i),
            )

        # Store subscriptions for later use
        self._subscriptions = subscriptions

    def _create_info_panel(self) -> Static:
        """Create the information panel.

        Returns:
            Static widget with subscription statistics
        """
        # Get current subscriptions from app state
        subscriptions = self.app.state.subscriptions
        total_subs = len(subscriptions) if subscriptions else 0

        info_lines = []

        if total_subs == 0:
            info_lines.extend(
                [
                    "No subscriptions configured",
                    "",
                    "💡 Click 'Add New Subscription' to add your first subscription",
                    "💡 You can add multiple subscriptions for different purposes",
                ]
            )
        else:
            info_lines.append(f"Total Subscriptions: {total_subs}")

            # Get active subscription
            active_sub = self.app.state.active_subscription
            if active_sub:
                # Truncate long URLs for display
                display_url = active_sub
                if len(display_url) > 50:
                    display_url = display_url[:47] + "..."
                info_lines.append(f"Active: {display_url}")

            info_lines.extend(
                [
                    "",
                    "💡 Click 'Add New Subscription' to add more subscriptions",
                    "💡 Use table actions to manage existing subscriptions",
                ]
            )

        return Static("\n".join(info_lines))

    def _create_subscription_items(self) -> list:
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
            # Get subscriptions directly from the state
            self._subscriptions = app_state.subscriptions or []
            self._active_subscription = app_state.active_subscription or ""
        except Exception:
            self._subscriptions = []
            self._active_subscription = ""

    def _get_subscription_url(self, subscription) -> str:
        """Get URL from subscription object.

        Args:
            subscription: Subscription object or dict

        Returns:
            Subscription URL
        """
        if isinstance(subscription, dict):
            return subscription.get("url", str(subscription))
        elif hasattr(subscription, "url"):
            return subscription.url
        elif isinstance(subscription, str):
            return subscription
        else:
            return str(subscription)

    def _format_subscription_display(self, subscription) -> str:
        """Format subscription information for display.

        Args:
            subscription: Subscription object or dict

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

            # Try to get type and tags - handle both dict and object
            if isinstance(subscription, dict):
                sub_type = subscription.get(
                    "source_type", subscription.get("type", "unknown")
                )
                tags = subscription.get("tags", [])
            else:
                sub_type = getattr(
                    subscription,
                    "source_type",
                    getattr(subscription, "type", "unknown"),
                )
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
        self.app.notify("Opening subscription form...", severity="information")
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

    @on(DataTable.RowSelected)
    def on_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle table row selection."""
        # Get row from coordinate
        row = event.coordinate.row
        try:
            if 0 <= row < len(self._subscriptions):
                subscription = self._subscriptions[row]
                self.app.notify(
                    f"Selected: {subscription.url[:30]}...", severity="information"
                )
        except (ValueError, IndexError):
            pass

    @on(DataTable.CellSelected)
    def on_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle table cell selection."""
        # Get row and column from coordinate
        row = event.coordinate.row
        column = event.coordinate.column

        # Check if it's the Actions column (column 4)
        if column == 4:  # Actions column
            try:
                index = row  # Row index is the subscription index
                if 0 <= index < len(self._subscriptions):
                    subscription = self._subscriptions[index]
                    # Show action menu
                    self._show_action_menu(index, subscription)
            except (ValueError, IndexError):
                pass

    def _handle_subscription_result(self, result: bool | str) -> None:
        """Handle the result from the subscription form.

        Args:
            result: True if subscription was added successfully,
                   False if cancelled, or error message string
        """
        if result is True:
            # Reload subscriptions and refresh display
            self._load_subscriptions()
            # Pop this screen and push a new one to refresh
            self.app.pop_screen()
            from sboxmgr.tui.screens.subscription_manager import (
                SubscriptionManagerScreen,
            )

            self.app.push_screen(SubscriptionManagerScreen())
            self.app.notify(
                "✅ Subscription added successfully! You can now manage it in the table.",
                severity="success",
            )
        elif isinstance(result, str):
            # Handle error case
            self.app.notify(f"❌ Error adding subscription: {result}", severity="error")
        else:
            # User cancelled
            self.app.notify("Subscription addition cancelled", severity="information")

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
                app_state.active_subscription = url
                self._active_subscription = url

                # Refresh display
                self.refresh()
                self.app.notify("Subscription activated", severity="success")
        except (ValueError, IndexError) as e:
            self.app.notify(
                f"Failed to activate subscription: {str(e)}", severity="error"
            )

    def _show_action_menu(self, index: int, subscription) -> None:
        """Show action menu for subscription.

        Args:
            index: Subscription index
            subscription: Subscription object
        """
        # Store current selection for keyboard actions
        self._selected_index = index
        self._selected_subscription = subscription

        # Show notification with available actions
        url = (
            subscription.url[:30] + "..."
            if len(subscription.url) > 30
            else subscription.url
        )
        self.app.notify(
            f"Selected: {url}\nPress 'r' to remove, 't' to toggle, 'a' to activate",
            severity="information",
        )

    def on_key(self, event) -> None:
        """Handle keyboard events."""
        if hasattr(self, "_selected_index") and hasattr(self, "_selected_subscription"):
            if event.key == "r":
                self._handle_remove_subscription_by_index(self._selected_index)
            elif event.key == "t":
                self._handle_toggle_subscription(self._selected_index)
            elif event.key == "a":
                self._handle_activate_subscription_by_index(self._selected_index)

    def _handle_remove_subscription_by_index(self, index: int) -> None:
        """Handle subscription removal by index.

        Args:
            index: Subscription index
        """
        try:
            if 0 <= index < len(self._subscriptions):
                subscription = self._subscriptions[index]
                url = subscription.url

                # Remove from app state
                if self.app.state.remove_subscription(url):
                    self.app.notify(
                        f"Removed subscription: {url[:30]}...", severity="success"
                    )
                    # Reload the table
                    self.load_subscriptions()
                    # Update info panel
                    info_panel = self.query_one(".subscription-info Static")
                    if info_panel:
                        info_panel.update(self._create_info_panel())
                else:
                    self.app.notify("Failed to remove subscription", severity="error")
        except Exception as e:
            self.app.notify(f"Error removing subscription: {str(e)}", severity="error")

    def _handle_toggle_subscription(self, index: int) -> None:
        """Handle subscription toggle by index.

        Args:
            index: Subscription index
        """
        try:
            if 0 <= index < len(self._subscriptions):
                subscription = self._subscriptions[index]
                url = subscription.url

                # Toggle in profile if available
                if self.app.state.active_config:
                    subscription_urls = self.app.state.active_config.metadata.get(
                        "subscription_urls", {}
                    )
                    for sub_id, stored_url in subscription_urls.items():
                        if stored_url == url:
                            # Find and toggle the config
                            for config in self.app.state.active_config.subscriptions:
                                if config.id == sub_id:
                                    config.enabled = not config.enabled
                                    # Save the config
                                    self.app.state._save_active_config()
                                    status = "enabled" if config.enabled else "disabled"
                                    self.app.notify(
                                        f"Subscription {status}: {url[:30]}...",
                                        severity="success",
                                    )
                                    # Reload the table
                                    self.load_subscriptions()
                                    return

                self.app.notify("Could not toggle subscription", severity="warning")
        except Exception as e:
            self.app.notify(f"Error toggling subscription: {str(e)}", severity="error")

    def _handle_activate_subscription_by_index(self, index: int) -> None:
        """Handle subscription activation by index.

        Args:
            index: Subscription index
        """
        try:
            if 0 <= index < len(self._subscriptions):
                subscription = self._subscriptions[index]
                url = subscription.url

                # Set as active subscription
                self.app.state.active_subscription = url
                self.app.notify(
                    f"Activated subscription: {url[:30]}...", severity="success"
                )
                # Update info panel
                info_panel = self.query_one(".subscription-info Static")
                if info_panel:
                    info_panel.update(self._create_info_panel())
        except Exception as e:
            self.app.notify(
                f"Error activating subscription: {str(e)}", severity="error"
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
                success = app_state.remove_subscription(url)
                if success:
                    # Reload subscriptions and refresh display
                    self._load_subscriptions()
                    self.refresh()
                    self.app.notify("Subscription removed", severity="success")
                else:
                    self.app.notify("Failed to remove subscription", severity="error")
        except (ValueError, IndexError) as e:
            self.app.notify(
                f"Failed to remove subscription: {str(e)}", severity="error"
            )
