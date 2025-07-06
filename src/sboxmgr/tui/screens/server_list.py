"""Server list screen with exclusion management.

This module implements the server list screen that displays available
servers with checkboxes for inclusion/exclusion management.
"""

from typing import List, Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Static

from sboxmgr.tui.utils.formatting import format_server_info


class ServerListScreen(Screen):
    """Server list screen with exclusion management.

    This screen displays all available servers from subscriptions
    with checkboxes to include/exclude servers. It provides visual
    feedback about server status and allows batch operations.

    The screen implements the context-aware UI principle by showing
    server-specific information and exclusion controls.
    """

    CSS = """
    ServerListScreen {
        layout: vertical;
    }

    .server-list-container {
        layout: vertical;
        padding: 1;
        height: 1fr;
    }

    .server-list-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .server-list-info {
        background: $surface;
        color: $text;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }

    .server-list-scroll {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    .server-item {
        layout: horizontal;
        height: 3;
        padding: 0 1;
        margin-bottom: 1;
        border: solid $primary;
        background: $surface;
    }

    .server-item:hover {
        background: $primary-darken-3;
    }

    .server-item.excluded {
        background: $error-darken-3;
        color: $text-muted;
    }

    .server-checkbox {
        width: 4;
        margin-right: 1;
    }

    .server-info {
        width: 1fr;
        height: 3;
    }

    .server-protocol {
        color: $accent;
        text-style: bold;
    }

    .server-address {
        color: $text;
    }

    .server-tag {
        color: $text-muted;
        text-style: italic;
    }

    .server-stats {
        color: $text-muted;
        text-align: right;
        margin-right: 1;
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
        """Initialize the server list screen.

        Args:
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self._servers: List = []
        self._excluded_servers: set = set()

    def compose(self) -> ComposeResult:
        """Compose the server list screen layout.

        Returns:
            The composed result containing the server list widgets
        """
        yield Header()

        with Vertical(classes="server-list-container"):
            yield Static("Server Management", classes="server-list-title")

            # Info panel
            with Vertical(classes="server-list-info"):
                yield self._create_info_panel()

            # Server list or empty state
            if self._servers:
                with VerticalScroll(classes="server-list-scroll"):
                    yield from self._create_server_items()
            else:
                with Vertical(classes="empty-state"):
                    yield Static(
                        "No servers available.\nAdd a subscription to see servers here."
                    )

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("Select All", id="select_all", variant="default")
                yield Button("Select None", id="select_none", variant="default")
                yield Button("Apply Changes", id="apply_changes", variant="primary")
                yield Button("Back", id="back", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount event."""
        self._load_servers()
        self._load_exclusions()

    def _create_info_panel(self) -> Static:
        """Create the information panel.

        Returns:
            Static widget with server statistics
        """
        if not self._servers:
            return Static("No servers loaded")

        total_servers = len(self._servers)
        excluded_count = len(self._excluded_servers)
        included_count = total_servers - excluded_count

        info_text = (
            f"Total Servers: {total_servers}\n"
            f"Included: {included_count}\n"
            f"Excluded: {excluded_count}"
        )

        return Static(info_text)

    def _create_server_items(self) -> List:
        """Create server item widgets.

        Returns:
            List of server item widgets
        """
        items = []

        for i, server in enumerate(self._servers):
            server_id = self._get_server_id(server)
            is_excluded = server_id in self._excluded_servers

            # Create server item container
            item_classes = "server-item"
            if is_excluded:
                item_classes += " excluded"

            with Horizontal(classes=item_classes):
                # Checkbox for inclusion/exclusion
                checkbox = Checkbox(
                    value=not is_excluded, id=f"server_{i}", classes="server-checkbox"
                )
                items.append(checkbox)

                # Server information
                server_info = self._format_server_display(server)
                info_widget = Static(server_info, classes="server-info")
                items.append(info_widget)

                # Server statistics (if available)
                stats = self._get_server_stats(server)
                if stats:
                    stats_widget = Static(stats, classes="server-stats")
                    items.append(stats_widget)

        return items

    def _load_servers(self) -> None:
        """Load servers from the application state."""
        try:
            app_state = self.app.state
            # Get servers from active subscription
            if hasattr(app_state, "servers"):
                self._servers = app_state.servers or []
            elif hasattr(app_state, "get_servers"):
                self._servers = app_state.get_servers() or []
            else:
                self._servers = []
        except Exception:
            self._servers = []

    def _load_exclusions(self) -> None:
        """Load current exclusions from the application state."""
        try:
            app_state = self.app.state
            if hasattr(app_state, "excluded_servers"):
                self._excluded_servers = set(app_state.excluded_servers)
            elif hasattr(app_state, "exclusions"):
                self._excluded_servers = set(app_state.exclusions)
            else:
                self._excluded_servers = set()
        except Exception:
            self._excluded_servers = set()

    def _get_server_id(self, server) -> str:
        """Get unique identifier for a server.

        Args:
            server: Server object or dict

        Returns:
            Unique server identifier
        """
        # Handle dict objects
        if isinstance(server, dict):
            if "address" in server and "port" in server:
                return f"{server['address']}:{server['port']}"
            elif "server" in server and "server_port" in server:
                return f"{server['server']}:{server['server_port']}"
            else:
                return str(server)

        # Handle object attributes
        if hasattr(server, "address") and hasattr(server, "port"):
            return f"{server.address}:{server.port}"
        elif hasattr(server, "server") and hasattr(server, "server_port"):
            return f"{server.server}:{server.server_port}"
        else:
            # Fallback to string representation
            return str(server)

    def _format_server_display(self, server) -> str:
        """Format server information for display.

        Args:
            server: Server object or dict

        Returns:
            Formatted server information string
        """
        try:
            return format_server_info(server)
        except Exception:
            # Fallback formatting for dict objects
            if isinstance(server, dict):
                protocol = server.get("protocol", server.get("type", "UNKNOWN")).upper()
                address = server.get("address", server.get("server", "unknown"))
                port = server.get("port", server.get("server_port", "?"))
                tag = server.get("tag", server.get("name", ""))

                display = f"[{protocol}] {address}:{port}"
                if tag:
                    display += f" ({tag})"
                return display

            # Fallback for object attributes
            if hasattr(server, "type"):
                protocol = server.type.upper()
            else:
                protocol = "UNKNOWN"

            if hasattr(server, "address"):
                address = server.address
                port = getattr(server, "port", "?")
            elif hasattr(server, "server"):
                address = server.server
                port = getattr(server, "server_port", "?")
            else:
                address = "unknown"
                port = "?"

            return f"[{protocol}] {address}:{port}"

    def _get_server_stats(self, server) -> Optional[str]:
        """Get server statistics for display.

        Args:
            server: Server object

        Returns:
            Server statistics string or None
        """
        # This could be extended to show ping, speed, etc.
        # For now, just show basic info
        stats = []

        if hasattr(server, "meta") and server.meta:
            if "ping" in server.meta:
                stats.append(f"Ping: {server.meta['ping']}ms")
            if "speed" in server.meta:
                stats.append(f"Speed: {server.meta['speed']}")

        return " | ".join(stats) if stats else None

    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes.

        Args:
            event: The checkbox changed event
        """
        # Extract server index from checkbox ID
        checkbox_id = event.checkbox.id
        if not checkbox_id or not checkbox_id.startswith("server_"):
            return

        try:
            server_index = int(checkbox_id.replace("server_", ""))
            if 0 <= server_index < len(self._servers):
                server = self._servers[server_index]
                server_id = self._get_server_id(server)

                if event.value:
                    # Include server (remove from exclusions)
                    self._excluded_servers.discard(server_id)
                else:
                    # Exclude server (add to exclusions)
                    self._excluded_servers.add(server_id)

                # Update app state if available
                app_state = self.app.state
                if hasattr(app_state, "toggle_server_exclusion"):
                    app_state.toggle_server_exclusion(server_id)

                # Update visual state
                self._update_server_item_visual(server_index, not event.value)
        except (ValueError, IndexError):
            pass

    def _update_server_item_visual(self, server_index: int, is_excluded: bool) -> None:
        """Update visual state of a server item.

        Args:
            server_index: Index of the server
            is_excluded: Whether the server is excluded
        """
        # This would update the visual styling of the server item
        # Implementation depends on how Textual handles dynamic styling
        pass

    @on(Button.Pressed, "#select_all")
    def on_select_all_pressed(self) -> None:
        """Handle select all button press."""
        # Clear all exclusions
        self._excluded_servers.clear()

        # Update all checkboxes
        for i in range(len(self._servers)):
            checkbox = self.query_one(f"#server_{i}", Checkbox)
            checkbox.value = True

        self.app.notify("All servers selected", severity="info")

    @on(Button.Pressed, "#select_none")
    def on_select_none_pressed(self) -> None:
        """Handle select none button press."""
        # Add all servers to exclusions
        for server in self._servers:
            server_id = self._get_server_id(server)
            self._excluded_servers.add(server_id)

        # Update all checkboxes
        for i in range(len(self._servers)):
            checkbox = self.query_one(f"#server_{i}", Checkbox)
            checkbox.value = False

        self.app.notify("All servers deselected", severity="info")

    @on(Button.Pressed, "#apply_changes")
    def on_apply_changes_pressed(self) -> None:
        """Handle apply changes button press."""
        try:
            # Update application state with new exclusions
            app_state = self.app.state
            if hasattr(app_state, "set_exclusions"):
                app_state.set_exclusions(list(self._excluded_servers))

            excluded_count = len(self._excluded_servers)
            total_count = len(self._servers)
            included_count = total_count - excluded_count

            self.app.notify(
                f"Applied changes: {included_count} servers included, {excluded_count} excluded",
                severity="success",
            )
            self.app.pop_screen()
        except Exception as e:
            self.app.notify(f"Failed to apply changes: {str(e)}", severity="error")

    @on(Button.Pressed, "#back")
    def on_back_pressed(self) -> None:
        """Handle back button press."""
        self.app.pop_screen()
