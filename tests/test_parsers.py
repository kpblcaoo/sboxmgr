import json
import os

import pytest

from sboxmgr.subscription.parsers.base64_parser import Base64Parser
from sboxmgr.subscription.parsers.json_parser import JSONParser
from sboxmgr.subscription.parsers.singbox_parser import SingBoxParser
from sboxmgr.subscription.parsers.uri_list_parser import URIListParser

SS_BASE64 = "YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4"  # pragma: allowlist secret
SS_URI = "ss://aes-256-gcm:pass@example.com:8388#ssuri"  # pragma: allowlist secret
VMESS_JSON = (
    '{"type": "vmess", "address": "vm.com", "port": 443}'  # pragma: allowlist secret
)
MIXED_LIST = """
# comment
ss://YWVzLTI1Ni1nY206cGFzc0BleGFtcGxlLmNvbTo4Mzg4#emoji🚀?plugin=obfs  # pragma: allowlist secret
vmess://eyJhZGQiOiJ2bS5jb20iLCJwb3J0Ijo0NDN9  # pragma: allowlist secret
ss://aes-256-gcm:pass@example.com:8388#ssuri  # pragma: allowlist secret
"""
INVALID = "not a valid subscription"

# SingBox test configurations
SINGBOX_BASIC = """
{
  "outbounds": [
    {
      "type": "shadowsocks",
      "server": "ss.example.com",
      "server_port": 8388,
      "method": "aes-256-gcm",
      "password": "password123",
      "tag": "ss-server"
    },
    {
      "type": "vmess",
      "server": "vm.example.com",
      "server_port": 443,
      "uuid": "12345678-1234-1234-1234-123456789012",
      "security": "auto",
      "tag": "vmess-server"
    }
  ]
}
"""

SINGBOX_WITH_COMMENTS = """
// SingBox configuration with comments
{
  "_comment": "This is a test config",
  "outbounds": [
    {
      "type": "shadowsocks",
      "server": "ss.example.com",
      "server_port": 8388,
      "method": "aes-256-gcm", // encryption method
      "password": "password123",
      "tag": "ss-server"
    }
  ]
}
"""

SINGBOX_INVALID = """
{
  "outbounds": [
    {
      "type": "shadowsocks",
      "server": "ss.example.com",
      // Missing server_port
      "method": "aes-256-gcm",
      "password": "password123"
    }
  ]
}
"""


@pytest.mark.parametrize(
    "parser_cls, raw, should_fail, expect_ss",
    [
        (Base64Parser, SS_BASE64.encode(), False, True),
        (URIListParser, SS_URI.encode(), False, True),
        (JSONParser, VMESS_JSON.encode(), False, False),
        (URIListParser, MIXED_LIST.encode(), False, True),
        (Base64Parser, INVALID.encode(), True, False),
        (SingBoxParser, SINGBOX_BASIC.encode(), False, True),
        (SingBoxParser, SINGBOX_WITH_COMMENTS.encode(), False, True),
        (
            SingBoxParser,
            SINGBOX_INVALID.encode(),
            False,
            False,
        ),  # Should skip invalid outbound
    ],
)
def test_parsers_edge_cases(parser_cls, raw, should_fail, expect_ss):
    parser = parser_cls()
    if should_fail:
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parser.parse(raw)
    else:
        servers = parser.parse(raw)
        if expect_ss:
            assert any(s.type == "ss" for s in servers)
        # Проверяем emoji/tag только если реально есть в тестовых данных
        # (например, в MIXED_LIST, но не в SS_URI)
        # if parser_cls is URIListParser and ...: # можно добавить отдельный тест для emoji


def test_uri_list_parser_edge_cases():
    from sboxmgr.subscription.parsers.uri_list_parser import URIListParser

    parser = URIListParser()
    # Правильный путь от корня проекта
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(project_root, "src/sboxmgr/examples/example_uri_list.txt")
    with open(file_path, "rb") as f:
        raw = f.read()
    servers = parser.parse(raw)
    # Проверяем, что все ожидаемые типы присутствуют
    types = {s.type for s in servers}
    assert "ss" in types
    assert "vless" in types
    assert "vmess" in types
    assert "trojan" in types
    # Проверяем, что хотя бы один тег содержит emoji или unicode
    assert any(
        "emoji" in (s.meta or {}).get("tag", "").lower()
        or "🚀" in (s.meta or {}).get("tag", "")
        for s in servers
    )
    # Проверяем, что парсер не падает на пустых строках, комментариях, невалидных строках
    # (если не выброшено исключение — тест пройден)


def test_singbox_parser_safe_field_injection():
    """Test that SingBoxParser uses safe field injection (SFI)."""
    parser = SingBoxParser()

    # Test with None values in metadata
    config_with_none = """
    {
      "outbounds": [
        {
          "type": "shadowsocks",
          "server": "ss.example.com",
          "server_port": 8388,
          "method": "aes-256-gcm",
          "password": null,
          "tag": null
        }
      ]
    }
    """

    servers = parser.parse(config_with_none.encode())
    assert len(servers) == 1
    server = servers[0]

    # Check that None values are filtered out
    assert "password" not in server.meta
    assert "tag" not in server.meta
    assert "origin" in server.meta
    assert "chain" in server.meta
    assert "server_id" in server.meta


def test_singbox_parser_fail_tolerance():
    """Test that SingBoxParser has proper fail-tolerance."""
    parser = SingBoxParser()

    # Test with missing server
    config_missing_server = """
    {
      "outbounds": [
        {
          "type": "shadowsocks",
          "server_port": 8388,
          "method": "aes-256-gcm",
          "password": "password123"
        }
      ]
    }
    """

    servers = parser.parse(config_missing_server.encode())
    assert len(servers) == 0

    # Test with missing port
    config_missing_port = """
    {
      "outbounds": [
        {
          "type": "shadowsocks",
          "server": "ss.example.com",
          "method": "aes-256-gcm",
          "password": "password123"
        }
      ]
    }
    """

    servers = parser.parse(config_missing_port.encode())
    assert len(servers) == 0

    # Test with invalid port
    config_invalid_port = """
    {
      "outbounds": [
        {
          "type": "shadowsocks",
          "server": "ss.example.com",
          "server_port": "invalid",
          "method": "aes-256-gcm",
          "password": "password123"
        }
      ]
    }
    """

    servers = parser.parse(config_invalid_port.encode())
    assert len(servers) == 0


def test_singbox_parser_metadata_unification():
    """Test that SingBoxParser provides unified metadata."""
    parser = SingBoxParser()

    config = """
    {
      "outbounds": [
        {
          "type": "shadowsocks",
          "server": "ss.example.com",
          "server_port": 8388,
          "method": "aes-256-gcm",
          "password": "password123",
          "tag": "test-tag"
        },
        {
          "type": "vmess",
          "server": "vm.example.com",
          "server_port": 443,
          "uuid": "12345678-1234-1234-1234-123456789012",
          "security": "auto",
          "tag": "vmess-tag"
        }
      ]
    }
    """

    servers = parser.parse(config.encode())
    assert len(servers) == 2

    # Check unified metadata structure
    for i, server in enumerate(servers):
        assert "origin" in server.meta
        assert server.meta["origin"] == "singbox"
        assert "chain" in server.meta
        assert server.meta["chain"] == "outbound"
        assert "server_id" in server.meta
        assert server.meta["server_id"].startswith(server.type)
        assert str(i) in server.meta["server_id"]


def test_singbox_parser_protocol_specific_fields():
    """Test that SingBoxParser handles protocol-specific fields correctly."""
    parser = SingBoxParser()

    config = """
    {
      "outbounds": [
        {
          "type": "vless",
          "server": "vl.example.com",
          "server_port": 443,
          "uuid": "12345678-1234-1234-1234-123456789012",
          "security": "tls",
          "flow": "xtls-rprx-vision"
        },
        {
          "type": "trojan",
          "server": "tr.example.com",
          "server_port": 443,
          "password": "trojan-pass",
          "flow": "xtls-rprx-vision"
        },
        {
          "type": "hysteria",
          "server": "hy.example.com",
          "server_port": 443,
          "auth": "hysteria-auth",
          "up_mbps": 100,
          "down_mbps": 100
        }
      ]
    }
    """

    servers = parser.parse(config.encode())
    assert len(servers) == 3

    # Check vless specific fields
    vless_server = next(s for s in servers if s.type == "vless")
    assert vless_server.meta["uuid"] == "12345678-1234-1234-1234-123456789012"
    assert vless_server.meta["security"] == "tls"
    assert vless_server.meta["flow"] == "xtls-rprx-vision"

    # Check trojan specific fields
    trojan_server = next(s for s in servers if s.type == "trojan")
    assert trojan_server.meta["password"] == "trojan-pass"
    assert trojan_server.meta["flow"] == "xtls-rprx-vision"
    assert trojan_server.security == "tls"

    # Check hysteria specific fields
    hysteria_server = next(s for s in servers if s.type == "hysteria")
    assert hysteria_server.meta["auth"] == "hysteria-auth"
    assert hysteria_server.meta["up_mbps"] == 100
    assert hysteria_server.meta["down_mbps"] == 100
    assert hysteria_server.security == "udp"
