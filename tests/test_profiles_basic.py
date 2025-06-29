"""
Basic tests for profile functionality (ADR-0017).

Tests the core profile models and CLI commands to ensure they work correctly.
"""

import json
import pytest
from pathlib import Path

from sboxmgr.profiles.models import (
    FullProfile, 
    SubscriptionProfile, 
    FilterProfile, 
    RoutingProfile, 
    ExportProfile,
    AgentProfile,
    UIProfile,
    ExportFormat,
    UIMode
)


class TestProfileModels:
    """Test Pydantic profile models."""
    
    def test_subscription_profile_creation(self):
        """Test creating a subscription profile."""
        sub = SubscriptionProfile(id="test_sub", enabled=True, priority=1)
        assert sub.id == "test_sub"
        assert sub.enabled is True
        assert sub.priority == 1
    
    def test_subscription_profile_validation(self):
        """Test subscription profile validation."""
        # Test priority validation
        with pytest.raises(ValueError, match="Priority must be >= 1"):
            SubscriptionProfile(id="test", priority=0)
    
    def test_full_profile_creation(self):
        """Test creating a full profile with minimal data."""
        profile = FullProfile(id="test_profile")
        
        assert profile.id == "test_profile"
        assert profile.version == "1.0"
        assert len(profile.subscriptions) == 0
        assert profile.export.format == ExportFormat.SINGBOX
        assert profile.routing.default_route == "tunnel"
    
    def test_full_profile_with_all_components(self):
        """Test creating a full profile with all components."""
        subscriptions = [
            SubscriptionProfile(id="sub1", enabled=True, priority=1),
            SubscriptionProfile(id="sub2", enabled=False, priority=2)
        ]
        
        filters = FilterProfile(
            exclude_tags=["ads", "test"],
            only_tags=["trusted"],
            exclusions=["server1"],
            only_enabled=True
        )
        
        routing = RoutingProfile(
            by_source={"sub1": "tunnel", "sub2": "direct"},
            default_route="tunnel"
        )
        
        export = ExportProfile(
            format=ExportFormat.CLASH,
            output_file="clash.yaml"
        )
        
        agent = AgentProfile(
            auto_restart=True,
            monitor_latency=False,
            health_check_interval="60s"
        )
        
        ui = UIProfile(
            default_language="ru",
            mode=UIMode.TUI,
            show_debug_info=True
        )
        
        profile = FullProfile(
            id="complete_profile",
            description="Complete test profile",
            subscriptions=subscriptions,
            filters=filters,
            routing=routing,
            export=export,
            agent=agent,
            ui=ui
        )
        
        assert profile.id == "complete_profile"
        assert len(profile.subscriptions) == 2
        assert profile.filters.exclude_tags == ["ads", "test"]
        assert profile.routing.by_source["sub1"] == "tunnel"
        assert profile.export.format == ExportFormat.CLASH
        assert profile.agent.auto_restart is True
        assert profile.ui.default_language == "ru"
    
    def test_profile_json_serialization(self):
        """Test profile JSON serialization and deserialization."""
        original = FullProfile(
            id="json_test",
            description="JSON test profile",
            subscriptions=[
                SubscriptionProfile(id="sub1", enabled=True, priority=1)
            ]
        )
        
        # Serialize to JSON
        json_data = original.model_dump_json()
        
        # Deserialize from JSON
        data = json.loads(json_data)
        restored = FullProfile(**data)
        
        assert restored.id == original.id
        assert restored.description == original.description
        assert len(restored.subscriptions) == len(original.subscriptions)
        assert restored.subscriptions[0].id == original.subscriptions[0].id
    
    def test_profile_validation_errors(self):
        """Test profile validation catches errors."""
        # Test empty ID
        with pytest.raises(ValueError, match="Profile ID cannot be empty"):
            FullProfile(id="")
        
        # Test extra fields are rejected
        with pytest.raises(ValueError):
            FullProfile(id="test", unknown_field="value")


class TestProfileExamples:
    """Test loading example profiles."""
    
    def test_load_home_profile(self):
        """Test loading the home.json example profile."""
        profile_path = Path(__file__).parent.parent / "examples" / "profiles" / "home.json"
        
        if not profile_path.exists():
            pytest.skip(f"Example profile not found: {profile_path}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profile = FullProfile(**data)
        
        assert profile.id == "home"
        assert "Pi-hole" in profile.description
        assert len(profile.subscriptions) == 2
        assert profile.export.format == ExportFormat.SINGBOX
        assert profile.ui.default_language == "ru"


@pytest.mark.integration
class TestProfileCLI:
    """Integration tests for profile CLI commands."""
    
    def test_profile_validate_command(self, tmp_path):
        """Test profile validate CLI command."""
        # Create a test profile
        profile_data = {
            "id": "cli_test",
            "description": "CLI test profile",
            "subscriptions": [
                {"id": "test_sub", "enabled": True, "priority": 1}
            ]
        }
        
        profile_file = tmp_path / "test_profile.json"
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2)
        
        # Import CLI command
        from sboxmgr.cli.commands.profile import _load_profile
        
        # Test loading the profile
        profile = _load_profile(str(profile_file))
        assert profile.id == "cli_test"
        assert len(profile.subscriptions) == 1 