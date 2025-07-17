"""Tests for protocol-specific validators."""

import pytest

from sboxmgr.subscription.models import ParsedServer, PipelineContext
from sboxmgr.subscription.validators.protocol_validator import (
    EnhancedRequiredFieldsValidator,
    ProtocolSpecificValidator,
    get_protocol_schema,
    validate_single_protocol_config,
)


def test_protocol_specific_validator():
    """Test protocol-specific validation."""
    validator = ProtocolSpecificValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)

    # Test valid Shadowsocks server
    valid_ss = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={"password": "test_password"},  # pragma: allowlist secret
    )

    # Test invalid Shadowsocks server (missing password)
    invalid_ss = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={},  # Missing password
    )

    servers = [valid_ss, invalid_ss]
    result = validator.validate(servers, context)

    # Should have validation errors but still return servers in tolerant mode
    assert len(result.errors) > 0
    assert len(result.valid_servers) == 2  # Both servers included in tolerant mode
    assert result.valid_servers[0] == valid_ss
    assert "validation_errors" in result.valid_servers[1].meta


def test_enhanced_required_fields_validator():
    """Test enhanced required fields validation."""
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)

    # Test valid server
    valid_server = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={"password": "test_password"},  # pragma: allowlist secret
    )

    # Test server with missing password
    invalid_server = ParsedServer(
        type="ss",
        address="example.com",
        port=8388,
        security="aes-256-gcm",
        meta={},  # Missing password
    )

    servers = [valid_server, invalid_server]
    result = validator.validate(servers, context)

    # Should have validation errors
    assert len(result.errors) > 0
    assert any("missing password" in error for error in result.errors)

    # Both servers should be included in tolerant mode
    assert len(result.valid_servers) == 2
    assert "validation_errors" in result.valid_servers[1].meta


def test_validate_single_protocol_config():
    """Test single protocol configuration validation."""
    # Valid Shadowsocks config
    valid_config = {
        "server": "example.com",
        "server_port": 8388,
        "password": "test_password",  # pragma: allowlist secret
        "method": "aes-256-gcm",
    }

    try:
        validated = validate_single_protocol_config(valid_config, "shadowsocks")
        assert validated is not None
    except Exception as e:
        pytest.fail(f"Valid config should not raise exception: {e}")

    # Invalid config (missing password)
    invalid_config = {
        "server": "example.com",
        "server_port": 8388,
        "method": "aes-256-gcm",
        # Missing password
    }

    with pytest.raises(Exception):
        validate_single_protocol_config(invalid_config, "shadowsocks")


def test_get_protocol_schema():
    """Test protocol schema generation."""
    # Test Shadowsocks schema
    schema = get_protocol_schema("shadowsocks")
    assert "properties" in schema
    assert "server" in schema["properties"]
    assert "server_port" in schema["properties"]
    assert "password" in schema["properties"]

    # Test unsupported protocol
    with pytest.raises(ValueError):
        get_protocol_schema("unsupported_protocol")


def test_protocol_validator_with_real_data():
    """Test protocol validator with real subscription data."""
    from sboxmgr.subscription.parsers.uri_list_parser import URIListParser

    # Test with example URI list
    test_data = b"""
# Test subscription
ss://aes-256-gcm:password@example.com:8388#TestSS  # pragma: allowlist secret
vless://uuid@host:443?encryption=none#TestVLESS
vmess://eyJ2IjoiMiIsInBzIjoiVGVzdCIsImFkZCI6IjEyNy4wLjAuMSIsInBvcnQiOiI0NDMiLCJpZCI6InV1aWQiLCJhaWQiOiIwIiwibmV0IjoidGNwIiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiJ9
"""

    # Parse servers
    parser = URIListParser()
    servers = parser.parse(test_data)

    # Validate with enhanced validator
    validator = EnhancedRequiredFieldsValidator()
    context = PipelineContext(mode="tolerant", debug_level=1)
    result = validator.validate(servers, context)

    # Should have some valid servers
    assert len(result.valid_servers) > 0

    # Check that we have different protocol types
    types = {s.type for s in result.valid_servers}
    assert "ss" in types
    assert "vless" in types
    assert "vmess" in types
