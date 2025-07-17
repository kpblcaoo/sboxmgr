"""
Basic tests for config functionality (ADR-0017).

Tests the core config models and CLI commands to ensure they work correctly.
"""

import json
from pathlib import Path

import pytest

from sboxmgr.configs.models import (
    AgentConfig,
    ExportConfig,
    ExportFormat,
    FilterConfig,
    RoutingConfig,
    SubscriptionConfig,
    UIConfig,
    UIMode,
    UserConfig,
)


class TestConfigModels:
    """Test Pydantic config models."""

    def test_subscription_config_creation(self):
        """Test creating a subscription config."""
        sub = SubscriptionConfig(id="test_sub", enabled=True, priority=1)
        assert sub.id == "test_sub"
        assert sub.enabled is True
        assert sub.priority == 1

    def test_subscription_config_validation(self):
        """Test subscription config validation."""
        # Test priority validation
        with pytest.raises(ValueError, match="Priority must be >= 1"):
            SubscriptionConfig(id="test", priority=0)

    def test_user_config_creation(self):
        """Test creating a user config with minimal data."""
        config = UserConfig(id="test_config")

        assert config.id == "test_config"
        assert config.version == "1.0"
        assert len(config.subscriptions) == 0
        assert config.export.format == ExportFormat.SINGBOX
        assert config.routing.default_route == "tunnel"

    def test_user_config_with_all_components(self):
        """Test creating a user config with all components."""
        subscriptions = [
            SubscriptionConfig(id="sub1", enabled=True, priority=1),
            SubscriptionConfig(id="sub2", enabled=False, priority=2),
        ]

        filters = FilterConfig(
            exclude_tags=["ads", "test"],
            only_tags=["trusted"],
            exclusions=["server1"],
            only_enabled=True,
        )

        routing = RoutingConfig(
            by_source={"sub1": "tunnel", "sub2": "direct"}, default_route="tunnel"
        )

        export = ExportConfig(format=ExportFormat.CLASH, output_file="clash.yaml")

        agent = AgentConfig(
            auto_restart=True, monitor_latency=False, health_check_interval="60s"
        )

        ui = UIConfig(default_language="ru", mode=UIMode.TUI, show_debug_info=True)

        config = UserConfig(
            id="complete_config",
            description="Complete test config",
            subscriptions=subscriptions,
            filters=filters,
            routing=routing,
            export=export,
            agent=agent,
            ui=ui,
        )

        assert config.id == "complete_config"
        assert len(config.subscriptions) == 2
        assert config.filters.exclude_tags == ["ads", "test"]
        assert config.routing.by_source["sub1"] == "tunnel"
        assert config.export.format == ExportFormat.CLASH
        assert config.agent.auto_restart is True
        assert config.ui.default_language == "ru"

    def test_config_json_serialization(self):
        """Test config JSON serialization and deserialization."""
        original = UserConfig(
            id="json_test",
            description="JSON test config",
            subscriptions=[SubscriptionConfig(id="sub1", enabled=True, priority=1)],
        )

        # Serialize to JSON
        json_data = original.model_dump_json()

        # Deserialize from JSON
        data = json.loads(json_data)
        restored = UserConfig(**data)

        assert restored.id == original.id
        assert restored.description == original.description
        assert len(restored.subscriptions) == len(original.subscriptions)
        assert restored.subscriptions[0].id == original.subscriptions[0].id

    def test_config_validation_errors(self):
        """Test config validation catches errors."""
        # Test empty ID
        with pytest.raises(ValueError, match="Config ID cannot be empty"):
            UserConfig(id="")

        # Test extra fields are rejected
        with pytest.raises(ValueError):
            UserConfig(id="test", unknown_field="value")


class TestConfigExamples:
    """Test loading example configs."""

    def test_load_home_config(self):
        """Test loading the home.json example config."""
        config_path = (
            Path(__file__).parent.parent / "examples" / "profiles" / "home.json"
        )

        if not config_path.exists():
            pytest.skip(f"Example config not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        config = UserConfig(**data)

        assert config.id == "home"
        assert "Pi-hole" in config.description
        assert len(config.subscriptions) == 2
        assert config.export.format == ExportFormat.SINGBOX
        assert config.ui.default_language == "ru"


@pytest.mark.integration
class TestConfigCLI:
    """Integration tests for config CLI commands."""

    def test_config_validate_command(self, tmp_path):
        """Test config validate CLI command."""
        # Create a test config
        config_data = {
            "id": "cli_test",
            "description": "CLI test config",
            "subscriptions": [{"id": "test_sub", "enabled": True, "priority": 1}],
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

        # Import CLI command
        from sboxmgr.configs.toml_support import load_config_auto

        # Test loading the config
        config = load_config_auto(config_file)
        assert config.id == "cli_test"
        assert len(config.subscriptions) == 1
