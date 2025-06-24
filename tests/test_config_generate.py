import pytest
import json
import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from sboxmgr.config.generate import generate_config, generate_temp_config, validate_config_file


class TestGenerateConfig:
    """Test generate_config function."""
    
    @pytest.fixture
    def sample_template(self):
        """Sample template for testing."""
        return {
            "outbounds": [
                {"type": "urltest", "tag": "auto", "outbounds": []},
                {"type": "direct", "tag": "direct"}
            ],
            "route": {
                "rules": [
                    {"ip_cidr": "$excluded_servers", "outbound": "direct"}
                ]
            }
        }
    
    @pytest.fixture
    def sample_outbounds(self):
        """Sample outbounds for testing."""
        return [
            {"type": "vless", "tag": "vless-1", "server": "test1.com"},
            {"type": "vmess", "tag": "vmess-1", "server": "test2.com"}
        ]
    
    def test_generate_config_template_not_found(self, tmp_path):
        """Test generate_config raises error when template not found."""
        template_file = tmp_path / "nonexistent.json"
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            generate_config([], str(template_file), str(config_file), str(backup_file), [])
    
    def test_generate_config_success(self, tmp_path, sample_template, sample_outbounds):
        """Test successful config generation."""
        # Create template file
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        excluded_ips = ["1.1.1.1", "2.2.2.2"]
        
        with patch('subprocess.run') as mock_run, \
             patch('sboxmgr.config.generate.info') as mock_info:
            
            mock_run.return_value = MagicMock(returncode=0)
            
            result = generate_config(
                sample_outbounds, str(template_file), str(config_file), 
                str(backup_file), excluded_ips
            )
            
            assert result is True
            assert config_file.exists()
            
            # Check generated config
            config_data = json.loads(config_file.read_text())
            assert len(config_data["outbounds"]) == 4  # urltest + 2 outbounds + direct
            assert config_data["outbounds"][0]["tag"] == "auto"
            assert config_data["outbounds"][0]["outbounds"] == ["vless-1", "vmess-1"]
            assert config_data["outbounds"][1]["tag"] == "vless-1"
            assert config_data["outbounds"][2]["tag"] == "vmess-1"
            
            # Check excluded IPs
            assert config_data["route"]["rules"][0]["ip_cidr"] == ["1.1.1.1/32", "2.2.2.2/32"]
            
            mock_info.assert_called()
            mock_run.assert_called_once()
    
    def test_generate_config_no_change(self, tmp_path, sample_template, sample_outbounds):
        """Test config generation when no changes needed."""
        # Create template file
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        
        # Pre-populate config file with expected content
        expected_config = sample_template.copy()
        expected_config["outbounds"] = [
            {"type": "urltest", "tag": "auto", "outbounds": ["vless-1", "vmess-1"]},
            sample_outbounds[0],
            sample_outbounds[1],
            {"type": "direct", "tag": "direct"}
        ]
        expected_config["route"]["rules"][0]["ip_cidr"] = []
        config_file.write_text(json.dumps(expected_config, indent=2))
        
        with patch('sboxmgr.config.generate.info') as mock_info:
            result = generate_config(
                sample_outbounds, str(template_file), str(config_file), 
                str(backup_file), []
            )
            
            assert result is False
            mock_info.assert_called_with("Configuration has not changed. Skipping update.")
    
    def test_generate_config_validation_failure(self, tmp_path, sample_template, sample_outbounds):
        """Test config generation with validation failure."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        
        with patch('subprocess.run') as mock_run, \
             patch('sboxmgr.config.generate.error') as mock_error:
            
            mock_run.side_effect = subprocess.CalledProcessError(1, "sing-box")
            
            with pytest.raises(subprocess.CalledProcessError):
                generate_config(
                    sample_outbounds, str(template_file), str(config_file), 
                    str(backup_file), []
                )
            
            mock_error.assert_called()
    
    def test_generate_config_singbox_not_found(self, tmp_path, sample_template, sample_outbounds):
        """Test config generation when sing-box not found."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        
        with patch('subprocess.run') as mock_run, \
             patch('sboxmgr.config.generate.error') as mock_error:
            
            mock_run.side_effect = FileNotFoundError("sing-box not found")
            
            result = generate_config(
                sample_outbounds, str(template_file), str(config_file), 
                str(backup_file), []
            )
            
            assert result is False
            mock_error.assert_called()
    
    def test_generate_config_config_dir_not_exists(self, tmp_path, sample_template, sample_outbounds):
        """Test config generation when config directory doesn't exist."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "nonexistent" / "config.json"
        backup_file = tmp_path / "backup.json"
        
        with pytest.raises(FileNotFoundError, match="Config directory does not exist"):
            generate_config(
                sample_outbounds, str(template_file), str(config_file), 
                str(backup_file), []
            )
    
    def test_generate_config_with_backup(self, tmp_path, sample_template, sample_outbounds):
        """Test config generation creates backup of existing config."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_file = tmp_path / "config.json"
        backup_file = tmp_path / "backup.json"
        
        # Create existing config
        existing_config = {"old": "config"}
        config_file.write_text(json.dumps(existing_config))
        
        with patch('subprocess.run') as mock_run, \
             patch('sboxmgr.config.generate.info') as mock_info:
            
            mock_run.return_value = MagicMock(returncode=0)
            
            result = generate_config(
                sample_outbounds, str(template_file), str(config_file), 
                str(backup_file), []
            )
            
            assert result is True
            assert backup_file.exists()
            
            # Check backup contains old config
            backup_data = json.loads(backup_file.read_text())
            assert backup_data == existing_config
            
            mock_info.assert_any_call(f"Created backup: {backup_file}")


class TestGenerateTempConfig:
    """Test generate_temp_config function."""
    
    @pytest.fixture
    def sample_template(self):
        """Sample template for testing."""
        return {
            "outbounds": [
                {"type": "urltest", "tag": "auto", "outbounds": []},
                {"type": "direct", "tag": "direct"}
            ],
            "route": {
                "rules": [
                    {"ip_cidr": "$excluded_servers", "outbound": "direct"}
                ]
            }
        }
    
    def test_generate_temp_config_success(self, tmp_path, sample_template):
        """Test successful temp config generation."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        outbounds = [{"type": "vless", "tag": "vless-1"}]
        excluded_ips = ["1.1.1.1"]
        
        config_json = generate_temp_config(outbounds, str(template_file), excluded_ips)
        
        config_data = json.loads(config_json)
        assert len(config_data["outbounds"]) == 3  # urltest + 1 outbound + direct
        assert config_data["outbounds"][0]["outbounds"] == ["vless-1"]
        assert config_data["route"]["rules"][0]["ip_cidr"] == ["1.1.1.1/32"]
    
    def test_generate_temp_config_template_not_found(self, tmp_path):
        """Test generate_temp_config with missing template."""
        template_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            generate_temp_config([], str(template_file), [])
    
    def test_generate_temp_config_empty_outbounds(self, tmp_path, sample_template):
        """Test generate_temp_config with empty outbounds."""
        template_file = tmp_path / "template.json"
        template_file.write_text(json.dumps(sample_template, indent=2))
        
        config_json = generate_temp_config([], str(template_file), [])
        
        config_data = json.loads(config_json)
        assert config_data["outbounds"][0]["outbounds"] == []
        assert config_data["route"]["rules"][0]["ip_cidr"] == []


class TestValidateConfigFile:
    """Test validate_config_file function."""
    
    def test_validate_config_file_success(self, tmp_path):
        """Test successful config validation."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"test": "config"}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, 
                stdout="Config is valid", 
                stderr=""
            )
            
            valid, output = validate_config_file(str(config_file))
            
            assert valid is True
            assert "Config is valid" in output
            mock_run.assert_called_once_with(
                ["sing-box", "check", "-c", str(config_file)], 
                capture_output=True, 
                text=True
            )
    
    def test_validate_config_file_invalid(self, tmp_path):
        """Test config validation failure."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"invalid": "config"}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout="", 
                stderr="Config is invalid"
            )
            
            valid, output = validate_config_file(str(config_file))
            
            assert valid is False
            assert "Config is invalid" in output
    
    def test_validate_config_file_singbox_not_found(self, tmp_path):
        """Test config validation when sing-box not found."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"test": "config"}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("sing-box not found")
            
            valid, output = validate_config_file(str(config_file))
            
            assert valid is False
            assert "sing-box executable not found" in output 