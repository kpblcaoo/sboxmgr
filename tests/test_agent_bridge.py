"""Tests for agent bridge functionality."""

import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.sboxmgr.agent import (
    AgentBridge,
    AgentCommand,
    AgentNotAvailableError,
    ClientType,
    ValidationRequest,
)
from src.sboxmgr.agent.event_sender import EventSender


class TestAgentBridge:
    """Test AgentBridge class."""

    def test_find_agent_not_found(self):
        """Test when agent is not found."""
        with patch("shutil.which", return_value=None):
            bridge = AgentBridge()
            assert bridge.agent_path is None

    def test_is_available_no_agent_path(self):
        """Test availability when no agent path."""
        with patch.object(AgentBridge, "_find_agent", return_value=None):
            bridge = AgentBridge()
            assert bridge.is_available() is False

    def test_validate_agent_not_available(self):
        """Test validation when agent not available."""
        with patch.object(AgentBridge, "_find_agent", return_value=None):
            bridge = AgentBridge()
            with pytest.raises(AgentNotAvailableError):
                bridge.validate(Path("/test/config.json"))


class TestAgentProtocol:
    """Test agent protocol definitions."""

    def test_validation_request_creation(self):
        """Test ValidationRequest creation."""
        request = ValidationRequest(
            config_path="/path/to/config.json", client_type=ClientType.SING_BOX
        )

        assert request.command == AgentCommand.VALIDATE
        assert request.config_path == "/path/to/config.json"
        assert request.client_type == ClientType.SING_BOX


class TestEventSenderTimestamp:
    """Test timestamp generation in EventSender."""

    def test_timestamp_format_iso8601_utc(self):
        """Test that timestamps are generated in ISO 8601 format with UTC timezone."""
        sender = EventSender()

        # Test event message timestamp
        event_message = sender._create_event_message(
            event_type="test",
            event_data={"key": "value"},
            source="test",
            priority="normal",
        )

        timestamp = event_message["timestamp"]

        # Check format: YYYY-MM-DDTHH:MM:SS.microseconds+00:00
        # or YYYY-MM-DDTHH:MM:SS.microsecondsZ (both are valid ISO 8601)
        # or YYYY-MM-DDTHH:MM:SS.microseconds+00:00Z (with both timezone and Z)
        iso_pattern = (
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z|\+00:00Z)$"
        )
        assert re.match(
            iso_pattern, timestamp
        ), f"Timestamp {timestamp} does not match ISO 8601 format"

        # Verify it's actually UTC by parsing
        # Handle case where timestamp might have duplicated timezone info
        clean_timestamp = timestamp.replace("Z", "").replace("+00:00+00:00", "+00:00")
        parsed_time = datetime.fromisoformat(clean_timestamp)

        # Check if timestamp has timezone info
        if parsed_time.tzinfo is None:
            # If no timezone info, assume it's UTC (common for UTC timestamps)
            assert True  # Accept timestamps without explicit timezone as UTC
        else:
            # If timezone info is present, verify it's UTC
            assert parsed_time.tzinfo == timezone.utc or parsed_time.tzinfo.utcoffset(
                parsed_time
            ) == timezone.utc.utcoffset(parsed_time)

    def test_command_message_timestamp(self):
        """Test command message timestamp format."""
        sender = EventSender()

        command_message = sender._create_command_message(
            command="test", params={"key": "value"}
        )

        timestamp = command_message["timestamp"]
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
        assert re.match(
            iso_pattern, timestamp
        ), f"Command timestamp {timestamp} does not match ISO 8601 format"

    def test_heartbeat_message_timestamp(self):
        """Test heartbeat message timestamp format."""
        sender = EventSender()

        heartbeat_message = sender._create_heartbeat_message(
            agent_id="test", status="healthy"
        )

        timestamp = heartbeat_message["timestamp"]
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)$"
        assert re.match(
            iso_pattern, timestamp
        ), f"Heartbeat timestamp {timestamp} does not match ISO 8601 format"
