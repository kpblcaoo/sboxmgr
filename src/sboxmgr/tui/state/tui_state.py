"""TUI application state management.

This module provides the main state class for the TUI application,
managing subscriptions, servers, and UI state in a centralized way.
Integrated with the profile system for persistent storage.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

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
    subscriptions: list[SubscriptionSource] = field(default_factory=list)
    active_subscription: Optional[str] = None

    # Server state
    servers: list[ParsedServer] = field(default_factory=list)
    excluded_servers: list[str] = field(default_factory=list)
    selected_servers: list[str] = field(default_factory=list)

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
                logger.debug(
                    f"[DEBUG] Configs directory contents: {list(self.config_manager.configs_dir.glob('*'))}"
                )
                self.config_manager._create_default_config()
                self.active_config = self.config_manager.get_active_config()
                logger.debug(f"Created default config: {self.active_config}")
            else:
                logger.debug(f"[DEBUG] Active config found: {self.active_config.id}")
                logger.debug(
                    f"[DEBUG] Active config subscriptions: {len(self.active_config.subscriptions)}"
                )
                logger.debug(
                    f"[DEBUG] Active config metadata keys: {list(self.active_config.metadata.keys())}"
                )

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

            # Set as active subscription if this is the first one
            if not self.active_subscription:
                self.active_subscription = url
                logger.debug(f"[DEBUG] Set active subscription to: {url}")

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
        if self.debug >= 2:
            logger.debug(
                f"[DEBUG] _save_subscription_to_profile called with URL: {url}, enabled: {enabled}"
            )
            logger.debug(
                f"[DEBUG] active_config.subscriptions before add: {self.active_config.subscriptions if self.active_config else None}"
            )
            logger.debug(
                f"[DEBUG] active_config.metadata before add: {self.active_config.metadata if self.active_config else None}"
            )
        if not self.active_config:
            logger.error("[ERROR] No active config available")
            return
        try:
            sub_id = f"sub_{len(self.active_config.subscriptions) + 1}"
            subscription_config = SubscriptionConfig(
                id=sub_id,
                enabled=enabled,
                priority=len(self.active_config.subscriptions) + 1,
            )
            self.active_config.subscriptions.append(subscription_config)
            if "subscription_urls" not in self.active_config.metadata:
                self.active_config.metadata["subscription_urls"] = {}
            self.active_config.metadata["subscription_urls"][sub_id] = url
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] active_config.subscriptions after add: {self.active_config.subscriptions}"
                )
                logger.debug(
                    f"[DEBUG] active_config.metadata after add: {self.active_config.metadata}"
                )
            self._save_active_config()
        except Exception as e:
            logger.error(f"[ERROR] Exception in _save_subscription_to_profile: {e}")
            import traceback

            traceback.print_exc()

    def _save_active_config(self) -> None:
        """Save the active configuration to file."""
        import traceback

        if self.debug >= 2:
            logger.debug("[DEBUG] _save_active_config called")
            logger.debug(f"[DEBUG] Call stack: {traceback.format_stack()[-3:]}")
            logger.debug(
                f"[DEBUG] active_config.subscriptions: {self.active_config.subscriptions if self.active_config else None}"
            )
            logger.debug(
                f"[DEBUG] active_config.metadata: {self.active_config.metadata if self.active_config else None}"
            )
        if not self.config_manager or not self.active_config:
            logger.error("[ERROR] Missing config_manager or active_config")
            logger.debug(f"[DEBUG] config_manager: {self.config_manager}")
            logger.debug(f"[DEBUG] active_config: {self.active_config}")
            return
        try:
            from datetime import datetime

            from sboxmgr.configs.toml_support import save_config_to_toml

            self.active_config.updated_at = datetime.now().isoformat()
            # Логируем, что реально будет сериализовано
            if self.debug >= 2:
                import pprint

                logger.debug(
                    f"[DEBUG] Will save config: {pprint.pformat(self.active_config.model_dump(exclude_none=True))}"
                )
            config_path = (
                self.config_manager.configs_dir / f"{self.active_config.id}.toml"
            )
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

            # Update active subscription if needed
            if self.active_subscription == url:
                if self.subscriptions:
                    # Set the first remaining subscription as active
                    self.active_subscription = self.subscriptions[0].url
                    logger.debug(
                        f"[DEBUG] Set new active subscription to: {self.active_subscription}"
                    )
                else:
                    # No subscriptions left
                    self.active_subscription = None
                    logger.debug("[DEBUG] No active subscription (all removed)")

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
        if self.debug >= 2:
            logger.debug("[DEBUG] _load_existing_data called")
        if not self.active_config:
            logger.debug("[DEBUG] No active config, skipping data loading")
            return
        try:
            subscription_urls = self.active_config.metadata.get("subscription_urls", {})
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] Found subscription URLs in metadata: {subscription_urls}"
                )
            for sub_id, url in subscription_urls.items():
                sub_config = None
                for sub in self.active_config.subscriptions:
                    if sub.id == sub_id:
                        sub_config = sub
                        break
                if self.debug >= 2:
                    logger.debug(f"[DEBUG] Found subscription config: {sub_config}")
                if sub_config and sub_config.enabled:
                    source = SubscriptionSource(url=url, source_type="url")
                    self.subscriptions.append(source)
                    if self.debug >= 2:
                        logger.debug(f"[DEBUG] Added subscription source: {source}")
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] Total subscriptions loaded: {len(self.subscriptions)}"
                )
            self._reload_servers()
            if self.debug >= 2:
                logger.debug(f"[DEBUG] Total servers loaded: {len(self.servers)}")
            saved_exclusions = self.active_config.metadata.get("excluded_servers", [])
            self.excluded_servers = saved_exclusions.copy()
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] Loaded {len(self.excluded_servers)} exclusions: {self.excluded_servers}"
                )
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

    def set_exclusions(self, exclusions: list[str]) -> None:
        """Set server exclusions and save to profile.

        Args:
            exclusions: List of server IDs to exclude
        """
        self.excluded_servers = exclusions.copy()
        if self.debug >= 2:
            logger.debug(f"[DEBUG] set_exclusions called with: {exclusions}")
            logger.debug(
                f"[DEBUG] active_config.subscriptions before exclusions: {self.active_config.subscriptions if self.active_config else None}"
            )
            logger.debug(
                f"[DEBUG] active_config.metadata before exclusions: {self.active_config.metadata if self.active_config else None}"
            )
        # Save to profile if available
        if self.active_config:
            self.active_config.metadata["excluded_servers"] = exclusions
            self._save_active_config()

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
        if self.debug >= 2:
            logger.debug(
                f"[DEBUG] generate_config called with output_path: {output_path}"
            )
            logger.debug(f"[DEBUG] active_config: {self.active_config}")
            logger.debug(f"[DEBUG] subscriptions count: {len(self.subscriptions)}")
            logger.debug(f"[DEBUG] excluded_servers: {self.excluded_servers}")

        if not self.active_config:
            logger.error("Error: No active profile configuration")
            return False

        if not self.subscriptions:
            logger.error("Error: No subscriptions available")
            return False

        try:
            # Get export settings from profile
            export_settings = self.get_export_settings()
            if self.debug >= 2:
                logger.debug(f"[DEBUG] Export settings: {export_settings}")

            # Use output path from profile if not specified
            if output_path == "config.json":
                output_path = export_settings.get("output_file", "config.json")

            # Convert UserConfig to FullProfile for orchestrator
            full_profile = self._convert_to_full_profile()
            if self.debug >= 2:
                logger.debug(f"[DEBUG] Converted to FullProfile: {full_profile}")

            # Collect all servers from all subscriptions
            all_servers = []
            for subscription in self.subscriptions:
                if self.debug >= 2:
                    logger.debug(f"[DEBUG] Processing subscription: {subscription.url}")

                # Get servers from this subscription
                servers_result = self.orchestrator.get_subscription_servers(
                    url=subscription.url,
                    source_type=subscription.source_type or "url",
                    exclusions=self.excluded_servers,
                )

                if servers_result.success and servers_result.config:
                    all_servers.extend(servers_result.config)
                    if self.debug >= 2:
                        logger.debug(
                            f"[DEBUG] Added {len(servers_result.config)} servers from {subscription.url}"
                        )
                else:
                    if self.debug >= 2:
                        logger.debug(
                            f"[DEBUG] Failed to get servers from {subscription.url}: {servers_result.errors}"
                        )

            if not all_servers:
                logger.error("Error: No servers available from any subscription")
                return False

            if self.debug >= 2:
                logger.debug(f"[DEBUG] Total servers collected: {len(all_servers)}")

            # TEMPORARY SOLUTION: Direct export manager usage for multiple subscriptions
            # TODO: Fix orchestrator.export_configuration() to support multiple subscriptions
            # This is a workaround until the core orchestrator supports multiple subscriptions
            # The CLI should also be updated to support multiple subscriptions properly
            #
            # Current issue: orchestrator.export_configuration() only accepts single source_url
            # Proper fix: Update orchestrator to accept list of subscriptions or multiple URLs
            #
            # Generate configuration using export manager directly with all servers
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] Calling export_manager.export with {len(all_servers)} servers"
                )
                logger.debug(
                    "[DEBUG] TEMPORARY: Using direct export_manager instead of orchestrator"
                )

            config = self.orchestrator.export_manager.export(
                servers=all_servers,
                exclusions=self.excluded_servers,
                user_routes=None,
                client_profile=None,
                profile=full_profile,
            )

            result = {
                "success": True,
                "format": export_settings["format"],
                "server_count": len(all_servers),
                "config": config,
                "metadata": {
                    "subscription_count": len(self.subscriptions),
                    "exclusions_applied": len(self.excluded_servers),
                },
            }

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
            if self.debug >= 2:
                logger.debug(
                    f"[DEBUG] Config file created successfully at: {output_path}"
                )
                logger.debug(
                    f"[DEBUG] Generated config with {result.get('server_count', 0)} servers from {result.get('metadata', {}).get('subscription_count', 0)} subscriptions"
                )
            return True

        except Exception as e:
            logger.error(f"Error generating configuration: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _convert_to_full_profile(self) -> Optional[Any]:
        """Convert UserConfig to FullProfile for orchestrator.

        Returns:
            FullProfile or None if conversion failed
        """
        if self.debug >= 2:
            logger.debug("[DEBUG] _convert_to_full_profile called")
            logger.debug(f"[DEBUG] active_config: {self.active_config}")

        if not self.active_config:
            logger.warning("[WARNING] No active config available")
            return None

        try:
            # Import FullProfile if available
            try:
                from sboxmgr.configs.models import FullProfile
            except ImportError:
                logger.warning("[WARNING] FullProfile not available")
                return None

            # Convert UserConfig to FullProfile
            # Note: This is a simplified conversion - in a real implementation,
            # you might want to map all fields properly
            full_profile = FullProfile(
                id=self.active_config.id,
                description=self.active_config.description,
                subscriptions=self.active_config.subscriptions,
                export=self.active_config.export,
                metadata=self.active_config.metadata,
                version=self.active_config.version,
                created_at=self.active_config.created_at,
                updated_at=self.active_config.updated_at,
            )

            if self.debug >= 2:
                logger.debug(f"[DEBUG] Converted to FullProfile: {full_profile}")
            return full_profile

        except Exception as e:
            logger.error(f"Error converting to FullProfile: {e}")
            import traceback

            traceback.print_exc()
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
