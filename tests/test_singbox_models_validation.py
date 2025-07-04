"""
Test sing-box Pydantic models against actual sing-box validation.

This test suite validates that our Pydantic models produce configurations
that are accepted by the actual sing-box binary.
"""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest
from src.sboxmgr.models import (
    SingBoxConfig, create_example_config, validate_singbox_config,
    LogLevel, DomainStrategy, Network,
    TlsConfig, MultiplexConfig, TransportConfig,
    DnsServer, DnsRule, DnsConfig,
    AuthenticationUser, AuthenticationConfig,
    NtpConfig,
    MixedInbound, SocksInbound, HttpInbound, ShadowsocksInbound,
    VmessInbound, VlessInbound, TrojanInbound, Hysteria2Inbound,
    WireGuardInbound, TuicInbound, ShadowTlsInbound, DirectInbound,
    ShadowsocksOutbound, VmessOutbound, VlessOutbound, TrojanOutbound,
    Hysteria2Outbound, WireGuardOutbound, HttpOutbound, SocksOutbound,
    TuicOutbound, ShadowTlsOutbound, DnsOutbound, DirectOutbound,
    BlockOutbound, SelectorOutbound, UrlTestOutbound,
    RouteRule, RouteConfig,
    ClashApiConfig, V2RayApiConfig, CacheFileConfig, ExperimentalConfig,
    ObservatoryConfig
)

def check_singbox_available() -> bool:
    """Check if sing-box binary is available for testing."""
    try:
        result = subprocess.run(
            ["sing-box", "version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def validate_with_singbox(config_dict: dict) -> bool:
    """Validate configuration with actual sing-box binary."""
    if not check_singbox_available():
        pytest.skip("sing-box binary not available")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f, indent=2)
        config_path = f.name
    
    try:
        result = subprocess.run(
            ["sing-box", "check", "-c", config_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    finally:
        Path(config_path).unlink(missing_ok=True)

class TestSingBoxModelsValidation:
    """Test sing-box Pydantic models validation."""
    
    def test_example_config_validation(self):
        """Test that example configuration validates correctly."""
        config_dict = create_example_config()
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_minimal_config_validation(self):
        """Test minimal valid configuration."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "direct",
                    "tag": "direct"
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_shadowsocks_config_validation(self):
        """Test Shadowsocks configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "shadowsocks",
                    "tag": "ss-out",
                    "server": "example.com",
                    "server_port": 8388,
                    "method": "aes-256-gcm",
                    "password": "secret"
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_vmess_config_validation(self):
        """Test VMess configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "vmess",
                    "tag": "vmess-out",
                    "server": "example.com",
                    "server_port": 10086,
                    "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
                    "security": "auto"
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_hysteria2_config_validation(self):
        """Test Hysteria2 configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "hysteria2",
                    "tag": "hysteria2-out",
                    "server": "example.com",
                    "server_port": 443,
                    "password": "secret"
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_dns_config_validation(self):
        """Test DNS configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "dns": {
                "servers": [
                    {"tag": "google", "address": "8.8.8.8"},
                    {"tag": "cloudflare", "address": "1.1.1.1"}
                ],
                "rules": [
                    {"type": "default", "server": "google"}
                ],
                "final": "google"
            },
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "direct",
                    "tag": "direct"
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_routing_config_validation(self):
        """Test routing configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "shadowsocks",
                    "tag": "ss-out",
                    "server": "example.com",
                    "server_port": 8388,
                    "method": "aes-256-gcm",
                    "password": "secret"
                },
                {
                    "type": "direct",
                    "tag": "direct"
                }
            ],
            "route": {
                "rules": [
                    {
                        "type": "default",
                        "domain": ["example.com"],
                        "outbound": "ss-out"
                    }
                ],
                "final": "direct"
            }
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_tls_config_validation(self):
        """Test TLS configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "vmess",
                    "tag": "vmess-out",
                    "server": "example.com",
                    "server_port": 443,
                    "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
                    "security": "auto",
                    "tls": {
                        "enabled": True,
                        "server_name": "example.com",
                        "insecure": False
                    }
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_transport_config_validation(self):
        """Test transport configuration validation."""
        config_dict = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "vmess",
                    "tag": "vmess-out",
                    "server": "example.com",
                    "server_port": 443,
                    "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
                    "security": "auto",
                    "transport": {
                        "network": "ws",
                        "ws_opts": {
                            "path": "/ws",
                            "headers": {
                                "Host": "example.com"
                            }
                        }
                    }
                }
            ]
        }
        
        # Test Pydantic validation
        config = SingBoxConfig.model_validate(config_dict)
        assert config is not None
        
        # Test sing-box binary validation
        assert validate_with_singbox(config_dict)
    
    def test_invalid_config_rejection(self):
        """Test that invalid configurations are properly rejected."""
        # Invalid Shadowsocks method
        invalid_config = {
            "log": {"level": "info"},
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                {
                    "type": "shadowsocks",
                    "tag": "ss-out",
                    "server": "example.com",
                    "server_port": 8388,
                    "method": "invalid-method",  # Invalid method
                    "password": "secret"
                }
            ]
        }
        
        # Should raise validation error
        with pytest.raises(Exception):
            SingBoxConfig.model_validate(invalid_config)
    
    def test_model_serialization(self):
        """Test that models can be serialized to JSON."""
        config_dict = create_example_config()
        config = SingBoxConfig.model_validate(config_dict)
        
        # Test serialization
        json_str = config.model_dump_json(indent=2)
        assert json_str is not None
        assert len(json_str) > 0
        
        # Test deserialization
        parsed_config = SingBoxConfig.model_validate_json(json_str)
        assert parsed_config is not None
    
    def test_schema_generation(self):
        """Test JSON schema generation."""
        schema = SingBoxConfig.generate_schema()
        assert schema is not None
        assert "properties" in schema
        assert "type" in schema
        assert schema["type"] == "object" 