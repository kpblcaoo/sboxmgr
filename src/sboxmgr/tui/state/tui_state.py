"""TUI application state management.

This module provides the main state class for the TUI application,
managing subscriptions, servers, and UI state in a centralized way.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from sboxmgr.core.orchestrator import Orchestrator
from sboxmgr.subscription.models import ParsedServer, SubscriptionSource


@dataclass
class TUIState:
    """Central state management for TUI application.

    This class maintains all the state needed for the TUI application,
    including subscription management, server lists, and UI preferences.

    Attributes:
        debug: Debug level for logging
        profile: Active profile name
        orchestrator: Core orchestrator instance
        subscriptions: List of subscription sources
        active_subscription: Currently active subscription URL
        servers: List of parsed servers
        excluded_servers: List of excluded server IDs
        selected_servers: List of selected server IDs for operations
        current_screen: Current screen identifier
        show_advanced: Whether to show advanced options
    """

    debug: int = 0
    profile: Optional[str] = None
    orchestrator: Orchestrator = field(default_factory=Orchestrator)

    # Subscription state
    subscriptions: List[SubscriptionSource] = field(default_factory=list)
    active_subscription: Optional[str] = None

    # Server state
    servers: List[ParsedServer] = field(default_factory=list)
    excluded_servers: List[str] = field(default_factory=list)
    selected_servers: List[str] = field(default_factory=list)

    # UI state
    current_screen: str = "welcome"
    show_advanced: bool = False

    def has_subscriptions(self) -> bool:
        """Check if user has any subscriptions.

        Returns:
            True if user has at least one subscription
        """
        return len(self.subscriptions) > 0

    def add_subscription(self, url: str, tags: Optional[List[str]] = None) -> bool:
        """Add new subscription source.

        Args:
            url: Subscription URL
            tags: Optional list of tags

        Returns:
            True if subscription was added successfully
        """
        try:
            # Determine source type based on URL
            source_type = "url_base64"  # Default type for most subscriptions
            if url.startswith(
                (
                    "vmess://",
                    "vless://",
                    "ss://",
                    "trojan://",
                    "tuic://",
                    "hysteria2://",
                )
            ):
                source_type = "uri_list"

            source = SubscriptionSource(url=url, source_type=source_type)
            # Store tags in metadata since SubscriptionSource doesn't have tags field
            if tags:
                source.label = ", ".join(tags)

            self.subscriptions.append(source)

            # Set as active if it's the first subscription
            if len(self.subscriptions) == 1:
                self.active_subscription = url

            return True
        except Exception:
            return False

    def remove_subscription(self, url: str) -> bool:
        """Remove subscription source.

        Args:
            url: Subscription URL to remove

        Returns:
            True if subscription was removed successfully
        """
        try:
            self.subscriptions = [s for s in self.subscriptions if s.url != url]

            # Clear active subscription if it was removed
            if self.active_subscription == url:
                self.active_subscription = None
                if self.subscriptions:
                    self.active_subscription = self.subscriptions[0].url

            return True
        except Exception:
            return False

    def get_subscription_count(self) -> int:
        """Get total number of subscriptions.

        Returns:
            Number of subscriptions
        """
        return len(self.subscriptions)

    def get_server_count(self) -> int:
        """Get total number of servers.

        Returns:
            Number of servers
        """
        return len(self.servers)

    def get_excluded_count(self) -> int:
        """Get number of excluded servers.

        Returns:
            Number of excluded servers
        """
        return len(self.excluded_servers)

    def toggle_server_exclusion(self, server_id: str) -> bool:
        """Toggle server exclusion status.

        Args:
            server_id: Server ID to toggle

        Returns:
            True if server is now excluded, False if included
        """
        if server_id in self.excluded_servers:
            self.excluded_servers.remove(server_id)
            return False
        else:
            self.excluded_servers.append(server_id)
            return True

    def is_server_excluded(self, server_id: str) -> bool:
        """Check if server is excluded.

        Args:
            server_id: Server ID to check

        Returns:
            True if server is excluded
        """
        return server_id in self.excluded_servers

    def clear_exclusions(self) -> None:
        """Clear all server exclusions."""
        self.excluded_servers.clear()

    def set_advanced_mode(self, enabled: bool) -> None:
        """Set advanced mode visibility.

        Args:
            enabled: Whether to show advanced options
        """
        self.show_advanced = enabled
