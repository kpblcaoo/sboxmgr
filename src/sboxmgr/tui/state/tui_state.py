"""TUI application state management.

This module provides the main state class for the TUI application,
managing subscriptions, servers, and UI state in a centralized way.
Integrated with the profile system for persistent storage.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from sboxmgr.core.orchestrator import Orchestrator
from sboxmgr.subscription.models import ParsedServer, SubscriptionSource

# Import profile system
try:
    from sboxmgr.configs.manager import ConfigManager
    from sboxmgr.configs.models import SubscriptionConfig, UserConfig

    PROFILES_AVAILABLE = True
except ImportError:
    ConfigManager = None
    UserConfig = None
    SubscriptionConfig = None
    PROFILES_AVAILABLE = False


# Setup logging for TUI debugging
def setup_tui_logging():
    """Setup logging for TUI debugging."""
    log_file = Path.home() / ".sboxmgr" / "tui_debug.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger specifically for TUI
    logger = logging.getLogger("tui_debug")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add file handler only (no console output)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_tui_logging()


@dataclass
class TUIState:
    """Central state management for TUI application.

    This class maintains all the state needed for the TUI application,
    including subscription management, server lists, and UI preferences.
    Now integrated with the profile system for persistent storage.

    Attributes:
        debug: Debug level for logging
        profile: Active profile name
        orchestrator: Core orchestrator instance
        config_manager: Profile configuration manager
        active_config: Current active profile configuration
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

    # Profile system integration
    config_manager: Optional[ConfigManager] = None
    active_config: Optional[UserConfig] = None

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

    def __post_init__(self):
        """Initialize state after dataclass creation."""
        if PROFILES_AVAILABLE:
            self._init_profile_system()
        self._load_existing_data()

    def _init_profile_system(self) -> None:
        """Initialize the profile system."""
        logger.debug("_init_profile_system called")

        try:
            logger.debug("Creating ConfigManager...")
            self.config_manager = ConfigManager()
            logger.debug(f"ConfigManager created: {self.config_manager}")
            logger.debug(f"Configs directory: {self.config_manager.configs_dir}")

            logger.debug("Getting active config...")
            self.active_config = self.config_manager.get_active_config()
            logger.debug(f"Active config: {self.active_config}")

            # If no active config, create default
            if not self.active_config:
                logger.debug("No active config found, creating default...")
                self.config_manager._create_default_config()
                self.active_config = self.config_manager.get_active_config()
                logger.debug(f"Created default config: {self.active_config}")

            if self.active_config:
                logger.debug(f"Active config ID: {self.active_config.id}")
                logger.debug(
                    f"Active config description: {self.active_config.description}"
                )
                logger.debug(
                    f"Active config subscriptions: {len(self.active_config.subscriptions)}"
                )
                logger.debug(
                    f"Active config metadata keys: {list(self.active_config.metadata.keys())}"
                )

        except Exception as e:
            logger.error(f"Exception in _init_profile_system: {e}", exc_info=True)
            self.config_manager = None
            self.active_config = None

    def add_subscription(self, url: str, enabled: bool = True) -> bool:
        """Add a new subscription and save to profile.

        Args:
            url: Subscription URL to add
            enabled: Whether subscription is enabled

        Returns:
            bool: True if subscription was added successfully
        """
        logger.debug(f"[DEBUG] Starting add_subscription for URL: {url}")
        logger.debug(f"[DEBUG] Enabled: {enabled}")
        logger.debug(f"[DEBUG] Current subscriptions count: {len(self.subscriptions)}")
        logger.debug(f"[DEBUG] Profile system available: {PROFILES_AVAILABLE}")
        logger.debug(f"[DEBUG] Config manager: {self.config_manager}")
        logger.debug(f"[DEBUG] Active config: {self.active_config}")

        try:
            logger.debug("[DEBUG] Calling orchestrator.get_subscription_servers...")
            # Validate URL with orchestrator
            result = self.orchestrator.get_subscription_servers(
                url=url, source_type="url"
            )

            logger.debug(f"[DEBUG] Orchestrator result - success: {result.success}")
            logger.debug(
                f"[DEBUG] Orchestrator result - config: {result.config is not None}"
            )
            if result.config:
                logger.debug(f"[DEBUG] Server count: {len(result.config)}")
            if hasattr(result, "errors") and result.errors:
                logger.debug(f"[DEBUG] Orchestrator errors: {result.errors}")

            if not result.success or not result.config:
                logger.error("[ERROR] Failed to get servers from subscription")
                if hasattr(result, "errors"):
                    logger.error(f"[ERROR] Errors: {result.errors}")
                return False

            logger.debug("[DEBUG] Creating subscription source...")
            # Create subscription source
            source = SubscriptionSource(url=url, source_type="url")
            logger.debug(f"[DEBUG] Created source: {source}")

            logger.debug("[DEBUG] Adding to local state...")
            # Add to local state
            self.subscriptions.append(source)
            self.servers.extend(result.config)
            logger.debug(f"[DEBUG] Added {len(result.config)} servers to local state")
            logger.debug(f"[DEBUG] Total subscriptions now: {len(self.subscriptions)}")
            logger.debug(f"[DEBUG] Total servers now: {len(self.servers)}")

            # Save to profile if available
            if self.config_manager and self.active_config:
                logger.debug("[DEBUG] Saving to profile...")
                self._save_subscription_to_profile(url, enabled)
                logger.debug("[DEBUG] Saved to profile successfully")
            else:
                logger.debug(
                    "[DEBUG] Profile system not available, skipping profile save"
                )

            logger.debug("[DEBUG] add_subscription completed successfully")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Exception in add_subscription: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _save_subscription_to_profile(self, url: str, enabled: bool = True) -> None:
        """Save subscription to active profile.

        Args:
            url: Subscription URL
            enabled: Whether subscription is enabled
        """
        logger.debug(
            f"[DEBUG] _save_subscription_to_profile called with URL: {url}, enabled: {enabled}"
        )

        if not self.active_config:
            logger.error("[ERROR] No active config available")
            return

        try:
            logger.debug(
                f"[DEBUG] Current subscriptions in profile: {len(self.active_config.subscriptions)}"
            )

            # Create subscription config
            sub_id = f"sub_{len(self.active_config.subscriptions) + 1}"
            logger.debug(f"[DEBUG] Creating subscription config with ID: {sub_id}")

            subscription_config = SubscriptionConfig(
                id=sub_id,
                enabled=enabled,
                priority=len(self.active_config.subscriptions) + 1,
            )
            logger.debug(f"[DEBUG] Created subscription config: {subscription_config}")

            # Add to active config
            self.active_config.subscriptions.append(subscription_config)
            logger.debug("[DEBUG] Added to active config subscriptions list")

            # Also store URL in metadata
            if "subscription_urls" not in self.active_config.metadata:
                self.active_config.metadata["subscription_urls"] = {}
                logger.debug("[DEBUG] Created subscription_urls in metadata")

            self.active_config.metadata["subscription_urls"][sub_id] = url
            logger.debug(f"[DEBUG] Stored URL in metadata: {sub_id} -> {url}")

            # Save config
            logger.debug("[DEBUG] Calling _save_active_config...")
            self._save_active_config()
            logger.debug("[DEBUG] _save_subscription_to_profile completed successfully")

        except Exception as e:
            logger.error(f"[ERROR] Exception in _save_subscription_to_profile: {e}")
            import traceback

            traceback.print_exc()

    def _save_active_config(self) -> None:
        """Save the active configuration to file."""
        logger.debug("[DEBUG] _save_active_config called")

        if not self.config_manager or not self.active_config:
            logger.error("[ERROR] Missing config_manager or active_config")
            logger.debug(f"[DEBUG] config_manager: {self.config_manager}")
            logger.debug(f"[DEBUG] active_config: {self.active_config}")
            return

        try:
            from datetime import datetime

            from sboxmgr.configs.toml_support import save_config_to_toml

            logger.debug("[DEBUG] Imported dependencies successfully")

            # Update timestamp
            self.active_config.updated_at = datetime.now().isoformat()
            logger.debug(f"[DEBUG] Updated timestamp: {self.active_config.updated_at}")

            # Save to file
            config_path = (
                self.config_manager.configs_dir / f"{self.active_config.id}.toml"
            )
            logger.debug(f"[DEBUG] Saving to path: {config_path}")

            save_config_to_toml(self.active_config, config_path)
            logger.debug("[DEBUG] _save_active_config completed successfully")

        except Exception as e:
            logger.error(f"[ERROR] Exception in _save_active_config: {e}")
            import traceback

            traceback.print_exc()

    def remove_subscription(self, url: str) -> bool:
        """Remove a subscription and update profile.

        Args:
            url: Subscription URL to remove

        Returns:
            bool: True if subscription was removed successfully
        """
        try:
            # Remove from local state
            self.subscriptions = [sub for sub in self.subscriptions if sub.url != url]

            # Remove from profile if available
            if self.config_manager and self.active_config:
                self._remove_subscription_from_profile(url)

            # Refresh servers
            self._reload_servers()
            return True

        except Exception as e:
            logger.error(f"Error removing subscription: {e}")
            return False

    def _remove_subscription_from_profile(self, url: str) -> None:
        """Remove subscription from active profile.

        Args:
            url: Subscription URL to remove
        """
        if not self.active_config:
            return

        try:
            # Find subscription ID by URL
            sub_id_to_remove = None
            if "subscription_urls" in self.active_config.metadata:
                for sub_id, stored_url in self.active_config.metadata[
                    "subscription_urls"
                ].items():
                    if stored_url == url:
                        sub_id_to_remove = sub_id
                        break

            if sub_id_to_remove:
                # Remove from subscriptions list
                self.active_config.subscriptions = [
                    sub
                    for sub in self.active_config.subscriptions
                    if sub.id != sub_id_to_remove
                ]

                # Remove from metadata
                del self.active_config.metadata["subscription_urls"][sub_id_to_remove]

                # Save config
                self._save_active_config()

        except Exception as e:
            logger.error(f"Error removing subscription from profile: {e}")

    def _reload_servers(self) -> None:
        """Reload servers from all subscriptions."""
        self.servers.clear()

        for subscription in self.subscriptions:
            try:
                result = self.orchestrator.get_subscription_servers(
                    url=subscription.url, source_type=subscription.source_type or "url"
                )
                if result.success and result.config:
                    self.servers.extend(result.config)
            except Exception as e:
                logger.error(f"Error reloading servers from {subscription.url}: {e}")

    def _load_existing_data(self) -> None:
        """Load existing subscriptions and data from profile."""
        logger.debug("[DEBUG] _load_existing_data called")

        if not self.active_config:
            logger.debug("[DEBUG] No active config, skipping data loading")
            return

        try:
            logger.debug("[DEBUG] Loading subscriptions from profile metadata...")
            # Load subscriptions from profile metadata
            subscription_urls = self.active_config.metadata.get("subscription_urls", {})
            logger.debug(
                f"[DEBUG] Found subscription URLs in metadata: {subscription_urls}"
            )

            for sub_id, url in subscription_urls.items():
                logger.debug(f"[DEBUG] Processing subscription {sub_id}: {url}")

                # Find corresponding subscription config
                sub_config = None
                for sub in self.active_config.subscriptions:
                    if sub.id == sub_id:
                        sub_config = sub
                        break

                logger.debug(f"[DEBUG] Found subscription config: {sub_config}")

                if sub_config and sub_config.enabled:
                    logger.debug(
                        "[DEBUG] Subscription is enabled, adding to local state"
                    )
                    source = SubscriptionSource(url=url, source_type="url")
                    self.subscriptions.append(source)
                    logger.debug(f"[DEBUG] Added subscription source: {source}")
                else:
                    logger.debug(
                        "[DEBUG] Subscription disabled or config not found, skipping"
                    )

            logger.debug(
                f"[DEBUG] Total subscriptions loaded: {len(self.subscriptions)}"
            )

            # Load servers from subscriptions
            logger.debug("[DEBUG] Reloading servers...")
            self._reload_servers()
            logger.debug(f"[DEBUG] Total servers loaded: {len(self.servers)}")

        except Exception as e:
            logger.error(f"[ERROR] Exception in _load_existing_data: {e}")
            import traceback

            traceback.print_exc()

    def has_subscriptions(self) -> bool:
        """Check if user has any subscriptions.

        Returns:
            True if user has at least one subscription
        """
        return len(self.subscriptions) > 0

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

    def generate_config(self, output_path: str = "config.json") -> bool:
        """Generate configuration using active profile and subscriptions.

        Args:
            output_path: Path where to save the generated configuration

        Returns:
            bool: True if configuration was generated successfully
        """
        if not self.active_config:
            logger.error("Error: No active profile configuration")
            return False

        if not self.subscriptions:
            logger.error("Error: No subscriptions available")
            return False

        try:
            # Use the first subscription for now
            # TODO: Support multiple subscriptions
            subscription = self.subscriptions[0]

            # Generate configuration using orchestrator
            result = self.orchestrator.export_configuration(
                source_url=subscription.url,
                source_type=subscription.source_type or "url",
                export_format=self.active_config.export.format,
                exclusions=self.excluded_servers,
            )

            if not result.get("success", False):
                logger.error(
                    f"Error generating configuration: {result.get('error', 'Unknown error')}"
                )
                return False

            config_data = result.get("config")
            if not config_data:
                logger.error("Error: No configuration data generated")
                return False

            # Save configuration
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                import json

                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error generating configuration: {e}")
            return False

    def _create_client_profile_from_config(self) -> Optional[Any]:
        """Create ClientProfile from active configuration.

        Returns:
            ClientProfile or None if creation failed
        """
        if not self.active_config or not self.active_config.export:
            return None

        try:
            from sboxmgr.subscription.models import ClientProfile, InboundProfile

            inbound_type = self.active_config.export.inbound_profile
            inbounds = []

            # Create inbound based on profile setting
            if inbound_type == "tun":
                inbounds.append(
                    InboundProfile(
                        type="tun",
                        options={
                            "tag": "tun-in",
                            "interface_name": "tun0",
                            "address": ["198.18.0.1/16"],
                            "mtu": 1500,
                            "auto_route": True,
                            "endpoint_independent_nat": True,
                            "stack": "system",
                            "sniff": True,
                            "strict_route": True,
                        },
                    )
                )
            elif inbound_type == "socks":
                inbounds.append(
                    InboundProfile(
                        type="socks",
                        listen="127.0.0.1",
                        port=1080,
                        options={
                            "tag": "socks-in",
                            "sniff": True,
                        },
                    )
                )
            elif inbound_type == "http":
                inbounds.append(
                    InboundProfile(
                        type="http",
                        listen="127.0.0.1",
                        port=8080,
                        options={"tag": "http-in", "sniff": True},
                    )
                )
            else:
                # Default to tun
                inbounds.append(
                    InboundProfile(
                        type="tun",
                        options={
                            "tag": "tun-in",
                            "interface_name": "tun0",
                            "address": ["198.18.0.1/16"],
                            "mtu": 1500,
                            "auto_route": True,
                            "endpoint_independent_nat": True,
                            "stack": "system",
                            "sniff": True,
                            "strict_route": True,
                        },
                    )
                )

            return ClientProfile(inbounds=inbounds)

        except Exception as e:
            logger.error(f"Error creating client profile: {e}")
            return None

    def get_active_profile_name(self) -> str:
        """Get the name of the active profile.

        Returns:
            str: Name of active profile or 'default' if none
        """
        if self.active_config:
            return self.active_config.id
        return "default"

    def get_export_settings(self) -> dict:
        """Get export settings from active profile.

        Returns:
            dict: Export settings
        """
        if self.active_config and self.active_config.export:
            return {
                "format": self.active_config.export.format,
                "inbound_profile": self.active_config.export.inbound_profile,
                "output_file": self.active_config.export.output_file,
                "outbound_profile": self.active_config.export.outbound_profile,
            }

        # Default settings
        return {
            "format": "sing-box",
            "inbound_profile": "tun",
            "output_file": "config.json",
            "outbound_profile": "vless-real",
        }

    def refresh_servers(self) -> None:
        """Refresh servers from the active subscription."""
        self.servers.clear()
        if not self.subscriptions:
            return
        for subscription in self.subscriptions:
            try:
                result = self.orchestrator.get_subscription_servers(
                    url=subscription.url, source_type=subscription.source_type or "url"
                )
                if result.success and result.config:
                    self.servers.extend(result.config)
            except Exception as e:
                logger.error(f"Error refreshing servers from {subscription.url}: {e}")
