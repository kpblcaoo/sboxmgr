"""Tests for agent bridge functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from src.sboxmgr.agent import AgentBridge, AgentNotAvailableError, ValidationRequest, ClientType, AgentCommand


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
            config_path="/path/to/config.json",
            client_type=ClientType.SING_BOX
        )
        
        assert request.command == AgentCommand.VALIDATE
        assert request.config_path == "/path/to/config.json"
        assert request.client_type == ClientType.SING_BOX

