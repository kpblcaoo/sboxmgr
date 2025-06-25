"""Tests for internal validation module.

Tests the replacement of subprocess sing-box validation with internal Pydantic validation.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.sboxmgr.validation import validate_config_dict, validate_config_json, SingBoxConfig
from src.sboxmgr.validation.internal import validate_config_file, validate_temp_config


class TestValidateConfigDict:
    """Test validate_config_dict function."""
    
    def test_valid_minimal_config(self):
        """Test validation of minimal valid configuration."""
        config = {
            "outbounds": [
                {"type": "direct", "tag": "direct"}
            ]
        }
        is_valid, message = validate_config_dict(config)
        assert is_valid is True
        assert "validation passed" in message.lower()
    
    def test_valid_complex_config(self):
        """Test validation of complex configuration with all fields."""
        config = {
            "log": {"level": "info"},
            "dns": {"servers": []},
            "inbounds": [
                {"type": "socks", "tag": "socks-in", "listen": "127.0.0.1", "listen_port": 1080}
            ],
            "outbounds": [
                {"type": "urltest", "tag": "auto", "outbounds": ["direct"]},
                {"type": "direct", "tag": "direct"}
            ],
            "route": {
                "rules": [
                    {"domain": ["example.com"], "outbound": "direct"}
                ],
                "final": "auto"
            },
            "experimental": {"cache_file": {"enabled": True}}
        }
        is_valid, message = validate_config_dict(config)
        assert is_valid is True
        assert "validation passed" in message.lower()
    
    def test_empty_outbounds_invalid(self):
        """Test that empty outbounds list is invalid."""
        config = {"outbounds": []}
        is_valid, message = validate_config_dict(config)
        assert is_valid is False
        assert "at least one outbound" in message.lower()
    
    def test_missing_outbounds_invalid(self):
        """Test that missing outbounds field is invalid."""
        config = {"log": {"level": "info"}}
        is_valid, message = validate_config_dict(config)
        assert is_valid is False
        assert "outbounds" in message.lower()
    
    def test_duplicate_outbound_tags_invalid(self):
        """Test that duplicate outbound tags are invalid."""
        config = {
            "outbounds": [
                {"type": "direct", "tag": "direct"},
                {"type": "urltest", "tag": "direct"}  # Duplicate tag
            ]
        }
        is_valid, message = validate_config_dict(config)
        assert is_valid is False
        assert "unique" in message.lower()
    
    def test_invalid_outbound_type(self):
        """Test that outbound without type is invalid."""
        config = {
            "outbounds": [
                {"tag": "direct"}  # Missing type
            ]
        }
        is_valid, message = validate_config_dict(config)
        assert is_valid is False
        assert "type" in message.lower()
    
    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed (extensibility)."""
        config = {
            "outbounds": [
                {
                    "type": "vless", 
                    "tag": "vless-out",
                    "server": "example.com",
                    "server_port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789abc",  # Extra field
                    "flow": "xtls-rprx-vision"  # Extra field
                }
            ]
        }
        is_valid, message = validate_config_dict(config)
        assert is_valid is True
        assert "validation passed" in message.lower()


class TestValidateConfigJson:
    """Test validate_config_json function."""
    
    def test_valid_json_string(self):
        """Test validation of valid JSON string."""
        config_json = '{"outbounds": [{"type": "direct", "tag": "direct"}]}'
        is_valid, message = validate_config_json(config_json)
        assert is_valid is True
        assert "validation passed" in message.lower()
    
    def test_invalid_json_syntax(self):
        """Test handling of invalid JSON syntax."""
        config_json = '{"outbounds": [{"type": "direct", "tag": "direct"}}'  # Missing closing brace
        is_valid, message = validate_config_json(config_json)
        assert is_valid is False
        assert "invalid json" in message.lower()
    
    def test_valid_json_invalid_config(self):
        """Test valid JSON but invalid configuration."""
        config_json = '{"outbounds": []}'  # Valid JSON, invalid config
        is_valid, message = validate_config_json(config_json)
        assert is_valid is False
        assert "at least one outbound" in message.lower()


class TestValidateConfigFile:
    """Test validate_config_file function."""
    
    def test_valid_config_file(self):
        """Test validation of valid configuration file."""
        config = {"outbounds": [{"type": "direct", "tag": "direct"}]}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            is_valid, message = validate_config_file(temp_path)
            assert is_valid is True
            assert "validation passed" in message.lower()
        finally:
            Path(temp_path).unlink()
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        is_valid, message = validate_config_file("/nonexistent/file.json")
        assert is_valid is False
        assert "not found" in message.lower()
    
    def test_directory_instead_of_file(self):
        """Test handling when path is directory instead of file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            is_valid, message = validate_config_file(temp_dir)
            assert is_valid is False
            assert "not a file" in message.lower()
    
    def test_invalid_json_file(self):
        """Test handling of file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_path = f.name
        
        try:
            is_valid, message = validate_config_file(temp_path)
            assert is_valid is False
            assert "invalid json" in message.lower()
        finally:
            Path(temp_path).unlink()


class TestValidateTempConfig:
    """Test validate_temp_config function."""
    
    def test_valid_temp_config(self):
        """Test validation of valid temporary configuration."""
        config_json = '{"outbounds": [{"type": "direct", "tag": "direct"}]}'
        # Should not raise exception
        validate_temp_config(config_json)
    
    def test_invalid_temp_config_raises_exception(self):
        """Test that invalid configuration raises ValueError."""
        config_json = '{"outbounds": []}'  # Invalid: empty outbounds
        
        with pytest.raises(ValueError) as exc_info:
            validate_temp_config(config_json)
        
        assert "validation failed" in str(exc_info.value).lower()
        assert "at least one outbound" in str(exc_info.value).lower()
    
    def test_invalid_json_raises_exception(self):
        """Test that invalid JSON raises ValueError."""
        config_json = '{"invalid": json}'  # Invalid JSON
        
        with pytest.raises(ValueError) as exc_info:
            validate_temp_config(config_json)
        
        assert "validation failed" in str(exc_info.value).lower()


class TestSingBoxConfigModel:
    """Test SingBoxConfig Pydantic model directly."""
    
    def test_minimal_config_creation(self):
        """Test creation of minimal configuration."""
        config = SingBoxConfig(outbounds=[{"type": "direct", "tag": "direct"}])
        assert len(config.outbounds) == 1
        assert config.outbounds[0].type == "direct"
        assert config.outbounds[0].tag == "direct"
    
    def test_complex_config_creation(self):
        """Test creation of complex configuration."""
        config_data = {
            "log": {"level": "info"},
            "outbounds": [
                {"type": "urltest", "tag": "auto", "outbounds": ["direct"]},
                {"type": "direct", "tag": "direct"}
            ],
            "route": {
                "rules": [
                    {"domain": ["example.com"], "outbound": "direct"},
                    {"rule_set": "geoip-ru", "outbound": "direct"},  # String rule_set
                    {"rule_set": ["geoip-us", "geoip-eu"], "outbound": "auto"}  # List rule_set
                ]
            }
        }
        
        config = SingBoxConfig(**config_data)
        assert config.log["level"] == "info"
        assert len(config.outbounds) == 2
        assert len(config.route.rules) == 3
        
        # Test rule_set flexibility
        assert config.route.rules[1].rule_set == "geoip-ru"  # String
        assert config.route.rules[2].rule_set == ["geoip-us", "geoip-eu"]  # List


class TestArchitectureDecoupling:
    """Test that we successfully decoupled from sing-box subprocess."""
    
    def test_no_subprocess_import_in_validation(self):
        """Test that validation module doesn't import subprocess."""
        import src.sboxmgr.validation.internal as internal_module
        import src.sboxmgr.validation.schema as schema_module
        
        # Check module source for subprocess imports
        import inspect
        
        internal_source = inspect.getsource(internal_module)
        schema_source = inspect.getsource(schema_module)
        
        assert "import subprocess" not in internal_source
        assert "from subprocess" not in internal_source
        assert "import subprocess" not in schema_source
        assert "from subprocess" not in schema_source
    
    def test_validation_works_without_singbox_binary(self):
        """Test that validation works even if sing-box binary is not available."""
        # This test ensures our internal validation doesn't depend on external binaries
        config = {
            "outbounds": [
                {"type": "vless", "tag": "vless1", "server": "example.com", "server_port": 443},
                {"type": "direct", "tag": "direct"}
            ],
            "route": {
                "rules": [
                    {"domain_suffix": [".ru"], "outbound": "direct"}
                ],
                "final": "vless1"
            }
        }
        
        is_valid, message = validate_config_dict(config)
        assert is_valid is True
        assert "validation passed" in message.lower()
        
        # Test that this would work in environments without sing-box installed
        # (This is the key architectural improvement) 