"""Tests for OutboundModel and related functionality."""

import pytest
from pydantic import ValidationError
from src.sboxmgr.subscription.validators.protocol_models import (
    OutboundModel,
    validate_outbound_config,
    generate_outbound_schema,
    convert_protocol_to_outbound,
    create_outbound_from_dict,
    ShadowsocksConfig,
    VmessConfig,
    VmessSettings,
    VmessUser,
    StreamSettings,
    TlsConfig
)


class TestOutboundModel:
    """Test OutboundModel functionality."""

    def test_shadowsocks_outbound_validation(self):
        """Test Shadowsocks outbound validation."""
        config = {
            "type": "shadowsocks",
            "server": "example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "test_password"
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.type == "shadowsocks"
        assert outbound.server == "example.com"
        assert outbound.server_port == 8388
        assert outbound.method == "aes-256-gcm"
        assert outbound.password == "test_password"

    def test_vmess_outbound_validation(self):
        """Test VMess outbound validation."""
        config = {
            "type": "vmess",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "security": "auto"
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.type == "vmess"
        assert outbound.server == "example.com"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"
        assert outbound.security == "auto"

    def test_vless_outbound_validation(self):
        """Test VLESS outbound validation."""
        config = {
            "type": "vless",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "flow": "xtls-rprx-vision"
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.type == "vless"
        assert outbound.server == "example.com"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"
        assert outbound.flow == "xtls-rprx-vision"

    def test_trojan_outbound_validation(self):
        """Test Trojan outbound validation."""
        config = {
            "type": "trojan",
            "server": "example.com",
            "server_port": 443,
            "password": "test_password"
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.type == "trojan"
        assert outbound.server == "example.com"
        assert outbound.server_port == 443
        assert outbound.password == "test_password"

    def test_wireguard_outbound_validation(self):
        """Test WireGuard outbound validation."""
        config = {
            "type": "wireguard",
            "server": "example.com",
            "server_port": 51820,
            "private_key": "test_private_key",
            "peer_public_key": "test_public_key"
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.type == "wireguard"
        assert outbound.server == "example.com"
        assert outbound.server_port == 51820
        assert outbound.private_key == "test_private_key"
        assert outbound.peer_public_key == "test_public_key"

    def test_invalid_outbound_type(self):
        """Test validation with invalid outbound type."""
        config = {
            "type": "invalid_type",
            "server": "example.com",
            "server_port": 443
        }
        
        with pytest.raises(ValueError, match="Unsupported outbound type"):
            validate_outbound_config(config)

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        config = {
            "type": "shadowsocks",
            "server": "example.com"
            # Missing server_port, method, password
        }
        
        with pytest.raises(ValueError, match="validation errors for ShadowsocksOutbound"):
            validate_outbound_config(config)

    def test_outbound_with_tls(self):
        """Test outbound with TLS configuration."""
        config = {
            "type": "vmess",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "alpn": ["h2", "http/1.1"]
            }
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.tls is not None
        assert outbound.tls.enabled is True
        assert outbound.tls.server_name == "example.com"
        assert outbound.tls.alpn == ["h2", "http/1.1"]

    def test_outbound_with_utls(self):
        """Test outbound with uTLS configuration."""
        config = {
            "type": "vmess",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "tls": {
                "enabled": True,
                "utls": {
                    "enabled": True,
                    "fingerprint": "chrome"
                }
            }
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.tls is not None
        assert outbound.tls.utls is not None
        assert outbound.tls.utls.enabled is True
        assert outbound.tls.utls.fingerprint == "chrome"

    def test_outbound_with_reality(self):
        """Test outbound with Reality configuration."""
        config = {
            "type": "vmess",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789012",
            "tls": {
                "enabled": True,
                "reality": {
                    "public_key": "test_public_key",
                    "short_id": "test_short_id"
                }
            }
        }
        
        outbound = validate_outbound_config(config)
        assert outbound.tls is not None
        assert outbound.tls.reality is not None
        assert outbound.tls.reality.public_key == "test_public_key"
        assert outbound.tls.reality.short_id == "test_short_id"


class TestOutboundConversion:
    """Test protocol to outbound conversion."""

    def test_convert_shadowsocks_to_outbound(self):
        """Test converting Shadowsocks config to outbound."""
        protocol_config = ShadowsocksConfig(
            server="example.com",
            server_port=8388,
            method="aes-256-gcm",
            password="test_password"
        )
        
        outbound = convert_protocol_to_outbound(protocol_config, tag="test_tag")
        assert outbound.type == "shadowsocks"
        assert outbound.tag == "test_tag"
        assert outbound.server == "example.com"
        assert outbound.server_port == 8388
        assert outbound.method == "aes-256-gcm"
        assert outbound.password == "test_password"

    def test_convert_vmess_to_outbound(self):
        """Test converting VMess config to outbound."""
        protocol_config = VmessConfig(
            server="example.com",
            server_port=443,
            settings=VmessSettings(
                clients=[VmessUser(id="12345678-1234-1234-1234-123456789012")]
            ),
            streamSettings=StreamSettings()
        )
        
        outbound = convert_protocol_to_outbound(protocol_config, tag="test_tag")
        assert outbound.type == "vmess"
        assert outbound.tag == "test_tag"
        assert outbound.server == "example.com"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"

    def test_convert_vmess_without_users(self):
        """Test converting VMess config without users."""
        protocol_config = VmessConfig(
            server="example.com",
            server_port=443,
            settings=VmessSettings(clients=[]),
            streamSettings=StreamSettings()
        )
        
        with pytest.raises(ValueError, match="VMess configuration must have at least one user"):
            convert_protocol_to_outbound(protocol_config)


class TestOutboundSchema:
    """Test outbound schema generation."""

    def test_generate_outbound_schema(self):
        """Test generating outbound schema."""
        schema = generate_outbound_schema()
        
        assert "properties" in schema
        assert "outbound" in schema["properties"]
        assert "discriminator" in schema["properties"]["outbound"]


class TestOutboundCreation:
    """Test outbound creation from dictionary."""

    def test_create_outbound_from_dict(self):
        """Test creating outbound from dictionary."""
        config = {
            "type": "shadowsocks",
            "server": "example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "test_password"
        }
        
        outbound = create_outbound_from_dict(config, tag="test_tag")
        assert outbound.tag == "test_tag"
        assert outbound.type == "shadowsocks"

    def test_create_outbound_without_tag(self):
        """Test creating outbound without tag."""
        config = {
            "type": "shadowsocks",
            "server": "example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "test_password"
        }
        
        outbound = create_outbound_from_dict(config)
        assert outbound.tag is None
        assert outbound.type == "shadowsocks" 