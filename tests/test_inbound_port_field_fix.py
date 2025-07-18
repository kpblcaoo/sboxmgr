"""Test for inbound port field mismatch fix.

This test verifies that the _convert_single_inbound function correctly handles
both 'listen_port' and 'port' fields in inbound configurations, ensuring
backward compatibility with existing configurations.
"""

from sboxmgr.models.singbox.inbounds import MixedInbound
from sboxmgr.subscription.exporters.singbox_exporter_v2.inbound_converter import (
    _convert_single_inbound,
)


def test_inbound_port_field_backward_compatibility():
    """Test that inbound conversion supports both listen_port and port fields."""
    # Test with listen_port field (existing sing-box format)
    config_with_listen_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "listen_port": 1080,
    }

    result_listen_port = _convert_single_inbound(config_with_listen_port)
    assert isinstance(result_listen_port, MixedInbound)
    assert result_listen_port.listen_port == 1080
    assert result_listen_port.listen == "127.0.0.1"
    assert result_listen_port.type == "mixed"

    # Test with port field (InboundProfile format)
    config_with_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "port": 8080,
    }

    result_port = _convert_single_inbound(config_with_port)
    assert isinstance(result_port, MixedInbound)
    assert result_port.listen_port == 8080
    assert result_port.listen == "127.0.0.1"
    assert result_port.type == "mixed"

    # Test that listen_port takes precedence over port
    config_both_fields = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "listen_port": 1080,
        "port": 8080,  # This should be ignored
    }

    result_both = _convert_single_inbound(config_both_fields)
    assert isinstance(result_both, MixedInbound)
    assert result_both.listen_port == 1080  # listen_port should take precedence
    assert result_both.listen == "127.0.0.1"
    assert result_both.type == "mixed"

    # Test default port when neither field is present
    config_no_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
    }

    result_no_port = _convert_single_inbound(config_no_port)
    assert isinstance(result_no_port, MixedInbound)
    assert result_no_port.listen_port == 7890  # Default port
    assert result_no_port.listen == "127.0.0.1"
    assert result_no_port.type == "mixed"


def test_inbound_port_field_with_different_types():
    """Test port field handling with different inbound types."""
    # Test SOCKS inbound
    socks_config = {
        "type": "socks",
        "tag": "socks-in",
        "listen": "127.0.0.1",
        "port": 1080,
        "users": [{"username": "user", "password": "pass"}],
    }

    result_socks = _convert_single_inbound(socks_config)
    assert result_socks.listen_port == 1080
    assert result_socks.type == "socks"

    # Test HTTP inbound
    http_config = {
        "type": "http",
        "tag": "http-in",
        "listen": "127.0.0.1",
        "listen_port": 8080,
        "users": [{"username": "user", "password": "pass"}],
    }

    result_http = _convert_single_inbound(http_config)
    assert result_http.listen_port == 8080
    assert result_http.type == "http"


def test_inbound_port_field_with_inboundprofile():
    """Test port field handling with InboundProfile objects."""
    from sboxmgr.subscription.models import InboundProfile

    # Create InboundProfile with port field (using supported type)
    inbound_profile = InboundProfile(
        type="socks",
        listen="127.0.0.1",
        port=1080,
        options={"tag": "socks-in"},
    )

    # Convert to dict and test
    inbound_dict = inbound_profile.model_dump()
    result = _convert_single_inbound(inbound_dict)

    assert result is not None
    assert result.listen_port == 1080
    assert result.listen == "127.0.0.1"
    assert result.type == "socks"


def test_inbound_port_field_edge_cases():
    """Test edge cases for port field handling."""
    # Test with None port (should use default)
    config_none_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "port": None,
    }

    result_none = _convert_single_inbound(config_none_port)
    assert result_none.listen_port == 7890  # Should use default when port is None

    # Test with zero port
    config_zero_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "port": 0,
    }

    result_zero = _convert_single_inbound(config_zero_port)
    assert result_zero.listen_port == 0  # Should preserve zero

    # Test with string port (should be converted to int)
    config_string_port = {
        "type": "mixed",
        "tag": "mixed-in",
        "listen": "127.0.0.1",
        "port": "1080",
    }

    result_string = _convert_single_inbound(config_string_port)
    assert result_string.listen_port == 1080  # Should be converted to int
