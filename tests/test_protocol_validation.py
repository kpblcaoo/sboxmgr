import pytest
from modules.protocol_validation import validate_protocol

def test_validate_protocol_valid():
    # Test for a valid protocol
    protocol = {
        "type": "vless",
        "server": "example.com",
        "server_port": 443,
        "uuid": "uuid-example",
        "tls": {
            "enabled": True,
            "server_name": "example.com"
        }
    }
    supported_protocols = ["vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"]
    result = validate_protocol(protocol, supported_protocols)
    assert result is not None
    assert result["type"] == "vless"
    assert result["server"] == "example.com"
    assert result["server_port"] == 443
    assert result["uuid"] == "uuid-example"
    assert result["tls"] == {"enabled": True, "server_name": "example.com"}
    assert "tag" in result

def test_validate_protocol_invalid():
    # Test for an invalid protocol
    protocol = {"type": "unknown"}
    supported_protocols = ["vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"]
    with pytest.raises(ValueError, match="Unsupported protocol: unknown"):
        validate_protocol(protocol, supported_protocols)