"""Server list screen with exclusion management.

This module implements the server list screen that displays available
servers with checkboxes for inclusion/exclusion management.
"""

from typing import Optional

from sboxmgr.tui.utils.formatting import format_server_info
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Footer, Header, Static


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
        height: 4;
        padding: 0 1;
        margin-bottom: 1;
        border: solid $primary;
        background: $surface;
        align: center middle;
    }

    .server-item:hover {
        background: $primary-darken-3;
        border: solid $accent;
    }

    .server-item.excluded {
        background: $error-darken-3;
        color: $text-muted;
        border: solid $error;
    }

    .server-checkbox {
        width: 4;
        height: 2;
        margin-right: 1;
        align: center middle;
    }

    .server-info {
        width: 1fr;
        height: 4;
        content-align: left middle;
        padding: 0 1;
    }

    .server-stats {
        color: $text-muted;
        text-align: right;
        margin-right: 1;
        align: center middle;
        width: 20;
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
        self._servers: list = []
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
                yield Static(self._create_info_panel())

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
                yield Button("Refresh Servers", id="refresh_servers", variant="default")
                yield Button("Select All", id="select_all", variant="default")
                yield Button("Select None", id="select_none", variant="default")
                yield Button("Apply Changes", id="apply_changes", variant="primary")
                yield Button("← Back", id="back", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount event."""
        # Always refresh servers from orchestrator/state
        if hasattr(self.app.state, "refresh_servers"):
            self.app.state.refresh_servers()
        self._load_servers()
        self._load_exclusions()
        # Обновляем layout с новыми данными
        self._update_server_layout()

    def _create_info_panel(self) -> str:
        """Create the information panel.

        Returns:
            String with server statistics
        """
        if not self._servers:
            return "No servers loaded"

        total_servers = len(self._servers)
        excluded_count = len(self._excluded_servers)
        included_count = total_servers - excluded_count

        info_text = (
            f"Total Servers: {total_servers}\n"
            f"Included: {included_count}\n"
            f"Excluded: {excluded_count}"
        )

        return info_text

    def _create_server_items(self) -> list:
        """Create server item widgets.

        Returns:
            List of server item widgets
        """
        items = []
        for i, server in enumerate(self._servers):
            server_id = self._get_server_id(server)
            is_excluded = server_id in self._excluded_servers
            item_classes = "server-item"
            if is_excluded:
                item_classes += " excluded"
            checkbox = Checkbox(
                value=not is_excluded, id=f"server_{i}", classes="server-checkbox"
            )
            server_info = self._format_server_display(server)
            info_widget = Static(server_info, classes="server-info")
            children = [checkbox, info_widget]
            stats = self._get_server_stats(server)
            if stats:
                stats_widget = Static(stats, classes="server-stats")
                children.append(stats_widget)
            server_item = Horizontal(*children, classes=item_classes)
            items.append(server_item)
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
        checkbox_id = event.checkbox.id
        if not checkbox_id or not checkbox_id.startswith("server_"):
            return
        try:
            server_index = int(checkbox_id.replace("server_", ""))
            if 0 <= server_index < len(self._servers):
                server = self._servers[server_index]
                server_id = self._get_server_id(server)
                if event.value:
                    self._excluded_servers.discard(server_id)
                else:
                    self._excluded_servers.add(server_id)
                # Сохраняем exclusions в app.state
                if hasattr(self.app.state, "set_exclusions"):
                    self.app.state.set_exclusions(list(self._excluded_servers))
                self._update_server_item_visual(server_index, not event.value)
                info_panel = self.query_one(".server-list-info Static")
                if info_panel:
                    info_panel.update(self._create_info_panel())
        except (ValueError, IndexError):
            pass

    def _update_server_item_visual(self, server_index: int, is_excluded: bool) -> None:
        """Update visual state of a server item.

        Args:
            server_index: Index of the server
            is_excluded: Whether the server is excluded
        """
        try:
            checkbox = self.query_one(f"#server_{server_index}", Checkbox)
            server_item = checkbox.parent
            if server_item:
                if is_excluded:
                    server_item.add_class("excluded")
                else:
                    server_item.remove_class("excluded")
                server_item.refresh()
        except Exception:
            self.refresh()

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

    @on(Button.Pressed, "#refresh_servers")
    def on_refresh_servers_pressed(self) -> None:
        """Handle refresh servers button press."""
        if hasattr(self.app.state, "refresh_servers"):
            self.app.state.refresh_servers()
        self._load_servers()
        # Обновляем layout с новыми данными
        self._update_server_layout()
        self.app.notify("Servers refreshed", severity="info")

    def on_key(self, event) -> None:
        """Handle arrow key navigation and space key for checkboxes."""
        if not self._servers:
            return
        if event.key == "space":
            # Найти чекбокс с фокусом
            focused_checkbox = None
            for i in range(len(self._servers)):
                try:
                    checkbox = self.query_one(f"#server_{i}", Checkbox)
                    if checkbox.has_focus:
                        focused_checkbox = checkbox
                        break
                except Exception:
                    continue
            if focused_checkbox:
                # Переключить состояние чекбокса
                focused_checkbox.value = not focused_checkbox.value
                return
            else:
                # Если ни один чекбокс не в фокусе, сфокусироваться на первом
                try:
                    first_checkbox = self.query_one("#server_0", Checkbox)
                    first_checkbox.focus()
                except Exception:
                    pass
                return
        # стрелки — как раньше
        current_index = None
        for i in range(len(self._servers)):
            try:
                checkbox = self.query_one(f"#server_{i}", Checkbox)
            except Exception:
                continue
            if checkbox.has_focus:
                current_index = i
                break
        if event.key == "down":
            next_index = (current_index + 1) if current_index is not None else 0
            if next_index < len(self._servers):
                try:
                    self.query_one(f"#server_{next_index}", Checkbox).focus()
                except Exception:
                    pass
        elif event.key == "up":
            prev_index = (
                (current_index - 1)
                if current_index is not None
                else len(self._servers) - 1
            )
            if prev_index >= 0:
                try:
                    self.query_one(f"#server_{prev_index}", Checkbox).focus()
                except Exception:
                    pass

    def _update_server_layout(self) -> None:
        """Update server list layout after data changes."""
        # Удаляем старый контент
        server_container = self.query_one(".server-list-container")
        if server_container:
            # Удаляем старые виджеты серверов
            for child in server_container.children:
                if (
                    hasattr(child, "classes")
                    and "server-list-scroll" in child.classes
                    or hasattr(child, "classes")
                    and "empty-state" in child.classes
                ):
                    child.remove()

            # Добавляем новый контент
            if self._servers:
                scroll = VerticalScroll(classes="server-list-scroll")
                server_container.mount(scroll)
                scroll.mount_all(self._create_server_items())
            else:
                empty_state = Vertical(classes="empty-state")
                server_container.mount(empty_state)
                empty_state.mount(
                    Static(
                        "No servers available.\nAdd a subscription to see servers here."
                    )
                )

        # Обновляем info panel
        info_panel = self.query_one(".server-list-info Static")
        if info_panel:
            info_panel.update(self._create_info_panel())
