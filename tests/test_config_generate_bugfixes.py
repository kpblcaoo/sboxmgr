"""Tests for config generation bugfixes."""

import json
import pytest
from unittest.mock import patch, mock_open, Mock
from sboxmgr.validation.internal import validate_temp_config
from sboxmgr.config.generate import generate_config


class TestConfigGenerateBugfixes:
    """Test suite for config generation bug fixes."""

    def test_validate_temp_config_json_string_input(self):
        """Test that validate_temp_config accepts JSON string, not dict."""
        # Valid JSON string
        config_json = '{"outbounds": [{"type": "direct", "tag": "direct"}]}'
        
        # Should not raise exception for valid config
        validate_temp_config(config_json)
        
        # Invalid JSON string should raise ValueError
        invalid_json = '{"outbounds": [invalid json}'
        with pytest.raises(ValueError, match="Configuration validation failed"):
            validate_temp_config(invalid_json)

    def test_orchestrator_creates_new_subscription_manager(self):
        """Test that Orchestrator always creates new SubscriptionManager for each URL."""
        from sboxmgr.core.orchestrator import Orchestrator
        from sboxmgr.subscription.models import SubscriptionSource, PipelineResult
        
        # Create orchestrator
        orchestrator = Orchestrator.create_default()
        
        # Mock the SubscriptionManager constructor to track calls
        with patch("sboxmgr.subscription.manager.SubscriptionManager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_result = PipelineResult(config=[], context=Mock(), errors=[], success=True)
            mock_manager_instance.get_servers.return_value = mock_result
            mock_manager_class.return_value = mock_manager_instance
            
            # Call get_subscription_servers with different URLs
            url1 = "http://example1.com/sub"
            url2 = "http://example2.com/sub"
            
            orchestrator.get_subscription_servers(url=url1)
            orchestrator.get_subscription_servers(url=url2)
            
            # Verify that SubscriptionManager was created twice with different sources
            assert mock_manager_class.call_count == 2
            
            # Verify that each call used the correct URL
            call1_source = mock_manager_class.call_args_list[0][0][0]
            call2_source = mock_manager_class.call_args_list[1][0][0]
            
            assert isinstance(call1_source, SubscriptionSource)
            assert isinstance(call2_source, SubscriptionSource)
            assert call1_source.url == url1
            assert call2_source.url == url2
