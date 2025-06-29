from sboxmgr.subscription.exporters.singbox_exporter import singbox_export
from sboxmgr.subscription.models import ParsedServer
import json

def test_singbox_exporter():
    servers = [
        ParsedServer(type="vmess", address="example.com", port=443, security="auto", meta={"uuid": "0000"}),  # pragma: allowlist secret
        ParsedServer(type="ss", address="127.0.0.1", port=8388, security="aes-256-gcm", meta={"password": "pass"}),  # pragma: allowlist secret
    ]
    config = singbox_export(servers, routes=[])
    config_json = json.dumps(config)
    assert "outbounds" in config_json
    assert "example.com" in config_json
    assert "127.0.0.1" in config_json

def test_export_wireguard_with_falsy_values():
    """Test that wireguard export correctly handles falsy values (0, False, None) in meta fields."""
    server = ParsedServer(
        type="wireguard",
        address="10.0.0.1",
        port=51820,
        private_key="private_key_test",  # pragma: allowlist secret
        peer_public_key="peer_public_key_test",  # pragma: allowlist secret
        local_address=["10.0.0.2/24"],
        meta={
            "mtu": 0,  # Falsy but valid value
            "keepalive": False,  # Falsy but valid value
        }
    )
    config = singbox_export([server], routes=[])
    config_json = json.dumps(config)
    
    # Check that falsy values are included in export
    assert "mtu" in config_json
    assert "keepalive" in config_json
    assert '"mtu": 0' in config_json
    assert '"keepalive": false' in config_json

def test_export_tuic_with_falsy_values():
    """Test that tuic export correctly handles falsy values in udp_relay_mode."""
    server = ParsedServer(
        type="tuic",
        address="10.0.0.1",
        port=443,
        uuid="test-uuid",
        password="test-password",  # pragma: allowlist secret
        meta={
            "udp_relay_mode": False,  # Falsy but valid value
        }
    )
    config = singbox_export([server], routes=[])
    config_json = json.dumps(config)
    
    # Check that falsy udp_relay_mode is included in export
    assert "udp_relay_mode" in config_json
    assert '"udp_relay_mode": false' in config_json

def test_export_with_none_values():
    """Test that export correctly handles None values in meta fields."""
    server = ParsedServer(
        type="wireguard",
        address="10.0.0.1",
        port=51820,
        private_key="private_key_test",  # pragma: allowlist secret
        peer_public_key="peer_public_key_test",  # pragma: allowlist secret
        local_address=["10.0.0.2/24"],
        meta={
            "mtu": None,  # None value
            "keepalive": None,  # None value
        }
    )
    config = singbox_export([server], routes=[])
    config_json = json.dumps(config)
    
    # Check that None values are NOT included in export (correct behavior)
    assert "mtu" not in config_json
    assert "keepalive" not in config_json

def test_export_outbound_without_tag():
    """Test that outbound without 'tag' does not cause KeyError and special outbounds are added."""
    server = ParsedServer(
        type="wireguard",
        address="10.0.0.1",
        port=51820,
        private_key="private_key_test",  # pragma: allowlist secret
        peer_public_key="peer_public_key_test",  # pragma: allowlist secret
        local_address=["10.0.0.2/24"],
        meta={}
    )
    config = singbox_export([server], routes=[])
    outbounds = config.get("outbounds", [])
    # Должны быть служебные outbounds (direct, block, dns-out)
    tags = {o.get("tag") for o in outbounds}
    assert "direct" in tags
    assert "block" in tags
    assert "dns-out" in tags 