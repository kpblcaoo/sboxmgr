"""Tests for sboxmgr.config.protocol module."""

from unittest.mock import patch

import pytest

from sboxmgr.config.protocol import validate_protocol


class TestValidateProtocol:
    """Test protocol validation functionality."""

    def test_validate_protocol_unsupported_protocol(self):
        """Test validation with unsupported protocol."""
        config = {"type": "unsupported_protocol"}
        supported_protocols = ["vless", "shadowsocks", "vmess"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Unsupported protocol: unsupported_protocol"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with("Unsupported protocol: unsupported_protocol")

    def test_validate_protocol_vless_complete(self):
        """Test VLESS protocol validation with all parameters."""
        config = {
            "type": "vless",
            "tag": "vless-out",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "flow": "xtls-rprx-direct",
            "tls": {"enabled": True},
        }
        supported_protocols = ["vless"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "vless",
            "tag": "vless-out",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "flow": "xtls-rprx-direct",
            "tls": {"enabled": True},
        }
        assert result == expected

    def test_validate_protocol_vless_minimal(self):
        """Test VLESS protocol validation with minimal parameters."""
        config = {
            "type": "vless",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vless"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "vless",
            "tag": "proxy-out",  # default tag
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        assert result == expected

    def test_validate_protocol_vless_missing_required_server(self):
        """Test VLESS protocol validation missing required server."""
        config = {
            "type": "vless",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vless"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for vless: server"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for vless: server"
        )

    def test_validate_protocol_vless_missing_required_uuid(self):
        """Test VLESS protocol validation missing required UUID."""
        config = {"type": "vless", "server": "example.com", "server_port": 443}
        supported_protocols = ["vless"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for vless: uuid"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with("Missing required parameter for vless: uuid")

    def test_validate_protocol_shadowsocks_complete(self):
        """Test Shadowsocks protocol validation with all parameters."""
        config = {
            "type": "shadowsocks",
            "tag": "ss-out",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "secret123",  # pragma: allowlist secret
            "network": "tcp",
        }
        supported_protocols = ["shadowsocks"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "shadowsocks",
            "tag": "ss-out",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "secret123",  # pragma: allowlist secret
            "network": "tcp",
        }
        assert result == expected

    def test_validate_protocol_shadowsocks_minimal(self):
        """Test Shadowsocks protocol validation with minimal parameters."""
        config = {
            "type": "shadowsocks",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "secret123",  # pragma: allowlist secret
        }
        supported_protocols = ["shadowsocks"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "shadowsocks",
            "tag": "proxy-out",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "aes-256-gcm",
            "password": "secret123",  # pragma: allowlist secret
        }
        assert result == expected

    def test_validate_protocol_shadowsocks_missing_method(self):
        """Test Shadowsocks protocol validation missing required method."""
        config = {
            "type": "shadowsocks",
            "server": "ss.example.com",
            "server_port": 8388,
            "password": "secret123",  # pragma: allowlist secret
        }
        supported_protocols = ["shadowsocks"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for shadowsocks: method"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for shadowsocks: method"
        )

    def test_validate_protocol_vmess_complete(self):
        """Test VMess protocol validation with all parameters."""
        config = {
            "type": "vmess",
            "tag": "vmess-out",
            "server": "vmess.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "security": "aes-128-gcm",
            "tls": {"enabled": True},
        }
        supported_protocols = ["vmess"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "vmess",
            "tag": "vmess-out",
            "server": "vmess.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "security": "aes-128-gcm",
            "tls": {"enabled": True},
        }
        assert result == expected

    def test_validate_protocol_vmess_default_security(self):
        """Test VMess protocol validation with default security."""
        config = {
            "type": "vmess",
            "server": "vmess.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vmess"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "vmess",
            "tag": "proxy-out",
            "server": "vmess.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "security": "auto",  # default value
        }
        assert result == expected

    def test_validate_protocol_trojan_complete(self):
        """Test Trojan protocol validation with all parameters."""
        config = {
            "type": "trojan",
            "tag": "trojan-out",
            "server": "trojan.example.com",
            "server_port": 443,
            "password": "trojan_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        supported_protocols = ["trojan"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "trojan",
            "tag": "trojan-out",
            "server": "trojan.example.com",
            "server_port": 443,
            "password": "trojan_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        assert result == expected

    def test_validate_protocol_trojan_missing_password(self):
        """Test Trojan protocol validation missing required password."""
        config = {"type": "trojan", "server": "trojan.example.com", "server_port": 443}
        supported_protocols = ["trojan"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for trojan: password"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for trojan: password"
        )

    def test_validate_protocol_tuic_complete(self):
        """Test TUIC protocol validation with all parameters."""
        config = {
            "type": "tuic",
            "tag": "tuic-out",
            "server": "tuic.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "password": "tuic_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        supported_protocols = ["tuic"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "tuic",
            "tag": "tuic-out",
            "server": "tuic.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "password": "tuic_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        assert result == expected

    def test_validate_protocol_tuic_without_password(self):
        """Test TUIC protocol validation without optional password."""
        config = {
            "type": "tuic",
            "server": "tuic.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["tuic"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "tuic",
            "tag": "proxy-out",
            "server": "tuic.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        assert result == expected

    def test_validate_protocol_hysteria2_complete(self):
        """Test Hysteria2 protocol validation with all parameters."""
        config = {
            "type": "hysteria2",
            "tag": "hy2-out",
            "server": "hy2.example.com",
            "server_port": 443,
            "password": "hy2_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        supported_protocols = ["hysteria2"]

        result = validate_protocol(config, supported_protocols)

        expected = {
            "type": "hysteria2",
            "tag": "hy2-out",
            "server": "hy2.example.com",
            "server_port": 443,
            "password": "hy2_password",  # pragma: allowlist secret
            "tls": {"enabled": True},
        }
        assert result == expected

    def test_validate_protocol_hysteria2_missing_password(self):
        """Test Hysteria2 protocol validation missing required password."""
        config = {"type": "hysteria2", "server": "hy2.example.com", "server_port": 443}
        supported_protocols = ["hysteria2"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for hysteria2: password"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for hysteria2: password"
        )

    def test_validate_protocol_no_handler_defined(self):
        """Test protocol validation with no handler defined (should not happen with match case)."""
        # This test covers the case _ branch, though it should be unreachable
        # due to the initial protocol check
        config = {"type": "unknown_protocol"}
        supported_protocols = [
            "unknown_protocol"
        ]  # Protocol is supported but no handler

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="No handler defined for protocol: unknown_protocol"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "No handler defined for protocol: unknown_protocol"
        )


class TestValidateProtocolEdgeCases:
    """Test edge cases and error conditions."""

    def test_validate_protocol_empty_config(self):
        """Test validation with empty config."""
        config = {}
        supported_protocols = ["vless"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(ValueError, match="Unsupported protocol: None"):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with("Unsupported protocol: None")

    def test_validate_protocol_none_values(self):
        """Test validation with None values for required fields."""
        config = {
            "type": "vless",
            "server": None,
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vless"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for vless: server"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for vless: server"
        )

    def test_validate_protocol_empty_string_values(self):
        """Test validation with empty string values for required fields."""
        config = {
            "type": "shadowsocks",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "",  # empty string
            "password": "secret123",  # pragma: allowlist secret
        }
        supported_protocols = ["shadowsocks"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for shadowsocks: method"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for shadowsocks: method"
        )

    def test_validate_protocol_zero_port(self):
        """Test validation with zero port (should be considered falsy)."""
        config = {
            "type": "vless",
            "server": "example.com",
            "server_port": 0,  # falsy value
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vless"]

        with patch("sboxmgr.config.protocol.error") as mock_error:
            with pytest.raises(
                ValueError, match="Missing required parameter for vless: server_port"
            ):
                validate_protocol(config, supported_protocols)

        mock_error.assert_called_once_with(
            "Missing required parameter for vless: server_port"
        )

    def test_validate_protocol_multiple_protocols_supported(self):
        """Test validation with multiple supported protocols."""
        config = {
            "type": "vmess",
            "server": "vmess.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
        }
        supported_protocols = ["vless", "vmess", "shadowsocks", "trojan"]

        result = validate_protocol(config, supported_protocols)

        assert result["type"] == "vmess"
        assert result["server"] == "vmess.example.com"
        assert result["security"] == "auto"  # default value

    def test_validate_protocol_complex_tls_config(self):
        """Test validation with complex TLS configuration."""
        config = {
            "type": "vless",
            "server": "example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": False,
                "alpn": ["h2", "http/1.1"],
            },
        }
        supported_protocols = ["vless"]

        result = validate_protocol(config, supported_protocols)

        assert result["tls"]["enabled"] is True
        assert result["tls"]["server_name"] == "example.com"
        assert result["tls"]["alpn"] == ["h2", "http/1.1"]


class TestValidateProtocolIntegration:
    """Integration tests with realistic scenarios."""

    def test_validate_protocol_all_supported_protocols(self):
        """Test validation with all supported protocols."""
        test_cases = [
            {
                "config": {
                    "type": "vless",
                    "server": "vless.example.com",
                    "server_port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789abc",
                },
                "expected_type": "vless",
            },
            {
                "config": {
                    "type": "shadowsocks",
                    "server": "ss.example.com",
                    "server_port": 8388,
                    "method": "aes-256-gcm",
                    "password": "secret123",  # pragma: allowlist secret
                },
                "expected_type": "shadowsocks",
            },
            {
                "config": {
                    "type": "vmess",
                    "server": "vmess.example.com",
                    "server_port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789abc",
                },
                "expected_type": "vmess",
            },
            {
                "config": {
                    "type": "trojan",
                    "server": "trojan.example.com",
                    "server_port": 443,
                    "password": "trojan_password",  # pragma: allowlist secret
                },
                "expected_type": "trojan",
            },
            {
                "config": {
                    "type": "tuic",
                    "server": "tuic.example.com",
                    "server_port": 443,
                    "uuid": "12345678-1234-1234-1234-123456789abc",
                },
                "expected_type": "tuic",
            },
            {
                "config": {
                    "type": "hysteria2",
                    "server": "hy2.example.com",
                    "server_port": 443,
                    "password": "hy2_password",  # pragma: allowlist secret
                },
                "expected_type": "hysteria2",
            },
        ]

        supported_protocols = [
            "vless",
            "shadowsocks",
            "vmess",
            "trojan",
            "tuic",
            "hysteria2",
        ]

        for test_case in test_cases:
            result = validate_protocol(test_case["config"], supported_protocols)
            assert result["type"] == test_case["expected_type"]
            assert result["tag"] == "proxy-out"  # default tag

    def test_validate_protocol_realistic_server_configs(self):
        """Test validation with realistic server configurations."""
        # Realistic VLESS config with XTLS
        vless_config = {
            "type": "vless",
            "tag": "vless-reality",
            "server": "reality.example.com",
            "server_port": 443,
            "uuid": "12345678-1234-1234-1234-123456789abc",
            "flow": "xtls-rprx-vision",
            "tls": {
                "enabled": True,
                "server_name": "www.microsoft.com",
                "reality": {
                    "enabled": True,
                    "public_key": "SLwVMXPeRCoEbIDNgYXqBaRE2KXVqoJgOsGRUY_-jFc",  # pragma: allowlist secret
                },
            },
        }

        # Realistic Shadowsocks config
        ss_config = {
            "type": "shadowsocks",
            "tag": "ss-2022",
            "server": "ss.example.com",
            "server_port": 8388,
            "method": "2022-blake3-aes-256-gcm",
            "password": "8JCsPssfgS8tiRwiMlhARg==",  # pragma: allowlist secret
            "network": "tcp",
        }

        supported_protocols = ["vless", "shadowsocks"]

        # Test VLESS
        vless_result = validate_protocol(vless_config, supported_protocols)
        assert vless_result["type"] == "vless"
        assert vless_result["flow"] == "xtls-rprx-vision"
        assert vless_result["tls"]["reality"]["enabled"] is True

        # Test Shadowsocks
        ss_result = validate_protocol(ss_config, supported_protocols)
        assert ss_result["type"] == "shadowsocks"
        assert ss_result["method"] == "2022-blake3-aes-256-gcm"
        assert ss_result["network"] == "tcp"
