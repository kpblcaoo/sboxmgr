import pytest
from unittest.mock import Mock, patch, MagicMock
from sboxmgr.utils.cli_common import load_outbounds, prepare_selection


class TestLoadOutbounds:
    """Test load_outbounds function."""
    
    def test_load_outbounds_dict_format(self):
        """Test loading outbounds from dict format."""
        json_data = {
            "outbounds": [
                {"type": "vless", "server": "example.com", "tag": "vless-1"},
                {"type": "direct", "tag": "direct"},
                {"type": "vmess", "server": "test.com", "tag": "vmess-1"},
                {"type": "unsupported", "server": "bad.com", "tag": "bad-1"}
            ]
        }
        supported_protocols = {"vless", "vmess", "trojan"}
        
        result = load_outbounds(json_data, supported_protocols)
        
        assert len(result) == 2
        assert result[0]["type"] == "vless"
        assert result[1]["type"] == "vmess"
        assert all(o["type"] in supported_protocols for o in result)
    
    def test_load_outbounds_list_format(self):
        """Test loading outbounds from list format."""
        json_data = [
            {"type": "vless", "server": "example.com", "tag": "vless-1"},
            {"type": "trojan", "server": "test.com", "tag": "trojan-1"},
            {"type": "unsupported", "server": "bad.com", "tag": "bad-1"}
        ]
        supported_protocols = {"vless", "trojan"}
        
        result = load_outbounds(json_data, supported_protocols)
        
        assert len(result) == 2
        assert result[0]["type"] == "vless"
        assert result[1]["type"] == "trojan"
    
    def test_load_outbounds_empty_data(self):
        """Test loading outbounds from empty data."""
        assert load_outbounds({}, {"vless"}) == []
        assert load_outbounds([], {"vless"}) == []
        assert load_outbounds({"outbounds": []}, {"vless"}) == []
    
    def test_load_outbounds_no_matching_protocols(self):
        """Test loading outbounds with no matching protocols."""
        json_data = {
            "outbounds": [
                {"type": "unsupported1", "tag": "bad-1"},
                {"type": "unsupported2", "tag": "bad-2"}
            ]
        }
        supported_protocols = {"vless", "vmess"}
        
        result = load_outbounds(json_data, supported_protocols)
        assert result == []


class TestPrepareSelectionBasic:
    """Test basic functionality of prepare_selection function."""
    
    def test_prepare_selection_empty_data_returns_empty(self):
        """Test prepare_selection with None data returns empty lists."""
        with patch('logging.error') as mock_error:
            outbounds, excluded_ips, selected_servers = prepare_selection(
                None, None, None, {"vless"}, {"exclusions": []}
            )
            
            assert outbounds == []
            assert excluded_ips == []
            assert selected_servers == []
            mock_error.assert_called_with("Error: URL is required for auto-selection.")
    
    def test_prepare_selection_exception_returns_empty(self):
        """Test prepare_selection handles exceptions gracefully."""
        # Mock select_config to raise exception
        with patch('sboxmgr.config.fetch.select_config', side_effect=Exception("Test error")), \
             patch('logging.error') as mock_error:
            
            json_data = {"outbounds": [{"type": "vless", "server": "test.com"}]}
            indices = [0]
            exclusions = {"exclusions": []}
            supported_protocols = {"vless"}
            
            outbounds, excluded_ips, selected_servers = prepare_selection(
                json_data, indices, None, supported_protocols, exclusions
            )
            
            # Should return empty lists on exception
            assert outbounds == []
            assert excluded_ips == []
            assert selected_servers == []
            mock_error.assert_called()
    
    def test_prepare_selection_with_debug_level(self):
        """Test prepare_selection logs debug information."""
        # Mock dependencies
        with patch('sboxmgr.config.fetch.select_config') as mock_select, \
             patch('sboxmgr.config.protocol.validate_protocol') as mock_validate, \
             patch('sboxmgr.utils.id.generate_server_id') as mock_id, \
             patch('typer.echo') as mock_echo, \
             patch('logging.info') as mock_info:
            
            # Setup mocks
            mock_select.return_value = {"type": "vless", "server": "test.com"}
            mock_validate.return_value = {"type": "vless", "server": "test.com", "tag": "vless-1"}
            mock_id.return_value = "test-id"
            
            json_data = {"outbounds": [{"type": "vless", "server": "test.com"}]}
            indices = [0]
            exclusions = {"exclusions": []}
            supported_protocols = {"vless"}
            
            prepare_selection(
                json_data, indices, None, supported_protocols, exclusions, 
                debug_level=2
            )
            
            # Should log debug information
            mock_info.assert_called()
            mock_echo.assert_called()
    
    def test_prepare_selection_auto_selection_no_valid_configs(self):
        """Test prepare_selection auto-selection with no valid configs."""
        with patch('sboxmgr.server.management.apply_exclusions') as mock_apply, \
             patch('sboxmgr.config.protocol.validate_protocol', side_effect=ValueError("Invalid")), \
             patch('logging.warning') as mock_warning:
            
            mock_apply.return_value = []
            
            json_data = {"outbounds": [{"type": "vless", "server": "invalid.com"}]}
            exclusions = {"exclusions": []}
            supported_protocols = {"vless"}
            
            outbounds, excluded_ips, selected_servers = prepare_selection(
                json_data, None, None, supported_protocols, exclusions
            )
            
            assert outbounds == []
            mock_warning.assert_called_with("No valid configurations found for auto-selection, using direct")
    
    def test_prepare_selection_with_exclusions_warning(self):
        """Test prepare_selection processes servers with exclusions."""
        with patch('sboxmgr.config.fetch.select_config') as mock_select, \
             patch('sboxmgr.config.protocol.validate_protocol') as mock_validate, \
             patch('sboxmgr.utils.id.generate_server_id') as mock_id:
            
            # Setup mocks
            mock_select.return_value = {"type": "vless", "server": "test.com"}
            mock_validate.return_value = {"type": "vless", "server": "test.com", "tag": "vless-1"}
            mock_id.return_value = "test-id"
            
            json_data = {"outbounds": [{"type": "vless", "server": "test.com"}]}
            indices = [0]
            exclusions = {"exclusions": [{"id": "other-id"}]}
            supported_protocols = {"vless"}
            
            outbounds, excluded_ips, selected_servers = prepare_selection(
                json_data, indices, None, supported_protocols, exclusions
            )
            
            # Should return the server successfully
            assert len(outbounds) == 1
            assert outbounds[0]["type"] == "vless"
            assert len(selected_servers) == 1 