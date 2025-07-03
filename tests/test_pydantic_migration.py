"""Tests for Pydantic migration - basic functionality check."""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import json

from src.sboxmgr.core.exclusions.models import ExclusionEntry, ExclusionList
from src.sboxmgr.core.exclusions.manager import ExclusionManager
from src.sboxmgr.subscription.models import SubscriptionSource, ParsedServer, PipelineContext, PipelineResult
from src.sboxmgr.subscription.errors import ErrorType, PipelineError
from src.sboxmgr.events.types import EventType, EventPriority, EventData
from src.sboxmgr.events.core import Event
from src.sboxmgr.core.orchestrator import OrchestratorConfig
from src.sboxmgr.profiles.models import FullProfile, SubscriptionProfile


class TestPydanticMigration:
    """Test basic functionality after Pydantic migration."""
    
    def test_exclusion_entry_pydantic(self):
        """Test ExclusionEntry with Pydantic."""
        entry = ExclusionEntry(id="test-server", name="Test Server", reason="Testing")
        
        # Test serialization (JSON mode for datetime compatibility)
        data = entry.model_dump(mode='json')
        assert data["id"] == "test-server"
        assert data["name"] == "Test Server"
        assert data["reason"] == "Testing"
        assert isinstance(data["timestamp"], str)  # JSON serialized datetime
        
        # Test deserialization
        entry2 = ExclusionEntry.model_validate(data)
        assert entry2.id == entry.id
        assert entry2.name == entry.name
        assert entry2.reason == entry.reason
    
    def test_exclusion_list_pydantic(self):
        """Test ExclusionList with Pydantic."""
        exc_list = ExclusionList()
        
        # Test adding entries
        entry1 = ExclusionEntry(id="server1", name="Server 1")
        entry2 = ExclusionEntry(id="server2", name="Server 2")
        
        assert exc_list.add(entry1) == True
        assert exc_list.add(entry2) == True
        assert exc_list.add(entry1) == False  # Duplicate
        
        # Test contains
        assert exc_list.contains("server1") == True
        assert exc_list.contains("server3") == False
        
        # Test remove
        assert exc_list.remove("server1") == True
        assert exc_list.remove("server1") == False  # Already removed
        
        # Test serialization (JSON mode)
        data = exc_list.model_dump(mode='json')
        assert data["version"] == 1
        assert len(data["exclusions"]) == 1
        assert data["exclusions"][0]["id"] == "server2"
        assert isinstance(data["last_modified"], str)  # JSON serialized datetime
        
        # Test deserialization
        exc_list2 = ExclusionList.model_validate(data)
        assert len(exc_list2.exclusions) == 1
        assert exc_list2.exclusions[0].id == "server2"
    
    def test_exclusion_manager_with_pydantic(self):
        """Test ExclusionManager with Pydantic models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "exclusions.json"
            manager = ExclusionManager(file_path=file_path)
            
            # Test add
            assert manager.add("server1", "Test Server 1", "Testing") == True
            assert manager.add("server2", "Test Server 2", "Testing") == True
            assert manager.add("server1", "Test Server 1", "Testing") == False  # Duplicate
            
            # Test contains
            assert manager.contains("server1") == True
            assert manager.contains("server3") == False
            
            # Test list
            exclusions = manager.list_all()
            assert len(exclusions) == 2
            assert exclusions[0]["id"] in ["server1", "server2"]
            
            # Test persistence (reload)
            manager2 = ExclusionManager(file_path=file_path)
            assert manager2.contains("server1") == True
            assert manager2.contains("server2") == True
    
    def test_subscription_models_pydantic(self):
        """Test subscription models with Pydantic."""
        # Test SubscriptionSource
        source = SubscriptionSource(
            url="https://example.com/sub",
            source_type="url_base64",
            headers={"User-Agent": "test"}
        )
        
        data = source.model_dump()
        assert data["url"] == "https://example.com/sub"
        assert data["source_type"] == "url_base64"
        assert data["headers"]["User-Agent"] == "test"
        
        source2 = SubscriptionSource.model_validate(data)
        assert source2.url == source.url
        assert source2.source_type == source.source_type
        
        # Test ParsedServer
        server = ParsedServer(
            type="vmess",
            address="example.com",
            port=443,
            uuid="test-uuid",
            tag="Test Server"
        )
        
        server_data = server.model_dump()
        assert server_data["type"] == "vmess"
        assert server_data["address"] == "example.com"
        assert server_data["port"] == 443
        assert server_data["uuid"] == "test-uuid"
        
        # Test PipelineContext
        context = PipelineContext(source="test", mode="strict")
        context_data = context.model_dump()
        assert context_data["source"] == "test"
        assert context_data["mode"] == "strict"
        assert "trace_id" in context_data
    
    def test_events_pydantic(self):
        """Test event models with Pydantic."""
        # Test EventData
        event_data = EventData(
            event_type=EventType.CONFIG_UPDATED,
            payload={"path": "/config.json"},
            source="test",
            timestamp=datetime.now(),
            priority=EventPriority.HIGH
        )
        
        data = event_data.model_dump(mode='json')  # Use JSON mode for enums
        assert data["event_type"] == "config.updated"
        assert data["payload"]["path"] == "/config.json"
        assert data["source"] == "test"
        assert data["priority"] == 80
        
        # Test Event
        event = Event(data=event_data)
        event.add_result("success")
        
        event_dump = event.model_dump()
        assert len(event_dump["results"]) == 1
        assert event_dump["results"][0] == "success"
        assert event_dump["cancelled"] == False
    
    def test_errors_pydantic(self):
        """Test error models with Pydantic."""
        error = PipelineError(
            type=ErrorType.VALIDATION,
            stage="parsing",
            message="Invalid format",
            context={"line": 10}
        )
        
        data = error.model_dump(mode='json')  # Use JSON mode for enums
        assert data["type"] == "validation"
        assert data["stage"] == "parsing"
        assert data["message"] == "Invalid format"
        assert data["context"]["line"] == 10
        assert isinstance(data["timestamp"], str)  # JSON serialized datetime
    
    def test_orchestrator_config_pydantic(self):
        """Test OrchestratorConfig with Pydantic."""
        config = OrchestratorConfig(
            default_mode="strict",
            debug_level=2,
            timeout_seconds=60
        )
        
        data = config.model_dump()
        assert data["default_mode"] == "strict"
        assert data["debug_level"] == 2
        assert data["timeout_seconds"] == 60
        assert data["cache_enabled"] == True  # Default
        assert data["fail_safe"] == True  # Default
    
    def test_profiles_pydantic(self):
        """Test profile models with Pydantic."""
        # Test SubscriptionProfile (only basic fields)
        sub_profile = SubscriptionProfile(
            id="test-subscription",
            enabled=True,
            priority=2
        )
        
        data = sub_profile.model_dump()
        assert data["id"] == "test-subscription"
        assert data["enabled"] == True
        assert data["priority"] == 2
        
        # Test FullProfile with SubscriptionProfile list
        full_profile = FullProfile(
            id="test-profile",
            description="Test profile",
            subscriptions=[sub_profile]
        )
        
        profile_data = full_profile.model_dump()
        assert profile_data["id"] == "test-profile"
        assert profile_data["description"] == "Test profile"
        assert "subscriptions" in profile_data
        assert len(profile_data["subscriptions"]) == 1
        assert profile_data["subscriptions"][0]["id"] == "test-subscription"
        
        # Test that default components are created
        assert "filters" in profile_data
        assert "routing" in profile_data
        assert "export" in profile_data
        assert profile_data["version"] == "1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 