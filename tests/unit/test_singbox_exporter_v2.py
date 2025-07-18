"""Tests for the new Sing-box exporter using modular Pydantic models.

This module tests the SingboxExporterV2 which uses the modular Pydantic models
from sboxmgr.models.singbox for better validation and type safety.
"""

import json

from sboxmgr.subscription.exporters.singbox_exporter_v2 import (
    SingboxExporterV2,
    convert_client_profile_to_inbounds,
    convert_parsed_server_to_outbound,
)
from sboxmgr.subscription.models import ClientProfile, InboundProfile, ParsedServer


class TestSingboxExporterV2:
    """Test cases for SingboxExporterV2."""

    def test_convert_shadowsocks_server(self):
        """Test conversion of Shadowsocks server to outbound."""
        server = ParsedServer(
            type="ss",
            address="1.2.3.4",
            port=8388,
            password="test_password",
            security="aes-256-gcm",
            tag="test-ss",
            meta={
                "name": "Test SS Server",
                "plugin": "obfs-local",
                "plugin_opts": {"obfs": "http", "obfs-host": "www.bing.com"},
            },
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "shadowsocks"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 8388
        assert outbound.method == "aes-256-gcm"
        assert outbound.password == "test_password"
        assert outbound.tag == "test-ss"
        assert outbound.plugin == "obfs-local"
        assert outbound.plugin_opts == {"obfs": "http", "obfs-host": "www.bing.com"}

    def test_convert_vmess_server(self):
        """Test conversion of VMess server to outbound."""
        server = ParsedServer(
            type="vmess",
            address="1.2.3.4",
            port=443,
            uuid="12345678-1234-1234-1234-123456789012",
            tag="test-vmess",
            meta={
                "network": "ws",
                "ws_path": "/path",
                "servername": "example.com",
                "alpn": ["h2", "http/1.1"],
            },
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "vmess"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"
        assert outbound.tls is not None
        assert outbound.tls.server_name == "example.com"
        assert outbound.tls.alpn == ["h2", "http/1.1"]
        assert outbound.transport is not None
        assert outbound.transport.type == "ws"
        assert outbound.transport.path == "/path"

    def test_convert_vless_server(self):
        """Test conversion of VLESS server to outbound."""
        server = ParsedServer(
            type="vless",
            address="1.2.3.4",
            port=443,
            uuid="12345678-1234-1234-1234-123456789012",
            tag="test-vless",
            meta={
                "network": "grpc",
                "grpc_service_name": "grpc",
                "flow": "xtls-rprx-vision",
                "servername": "example.com",
            },
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "vless"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"
        assert outbound.flow == "xtls-rprx-vision"
        assert outbound.tag == "test-vless"
        assert outbound.tls is not None
        assert outbound.tls.server_name == "example.com"
        assert outbound.transport is not None
        assert outbound.transport.type == "grpc"
        assert outbound.transport.service_name == "grpc"

    def test_convert_trojan_server(self):
        """Test conversion of Trojan server to outbound."""
        server = ParsedServer(
            type="trojan",
            address="1.2.3.4",
            port=443,
            password="test_password",
            tag="test-trojan",
            meta={"servername": "example.com", "alpn": ["h2", "http/1.1"]},
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "trojan"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 443
        assert outbound.password == "test_password"
        assert outbound.tag == "test-trojan"
        assert outbound.tls is not None
        assert outbound.tls.server_name == "example.com"
        assert outbound.tls.alpn == ["h2", "http/1.1"]

    def test_convert_hysteria2_server(self):
        """Test conversion of Hysteria2 server to outbound."""
        server = ParsedServer(
            type="hysteria2",
            address="1.2.3.4",
            port=443,
            password="test_password",
            tag="test-hysteria2",
            meta={
                "up_mbps": 100,
                "down_mbps": 100,
                "obfs": "salamander",
                "obfs_type": "salamander",
            },
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "hysteria2"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 443
        assert outbound.password == "test_password"
        assert outbound.tag == "test-hysteria2"
        assert outbound.up_mbps == 100
        assert outbound.down_mbps == 100
        assert outbound.obfs == "salamander"
        assert outbound.obfs_type == "salamander"

    def test_convert_wireguard_server(self):
        """Test conversion of WireGuard server to outbound."""
        server = ParsedServer(
            type="wireguard",
            address="1.2.3.4",
            port=51820,
            private_key="private_key_here",
            peer_public_key="peer_public_key_here",
            pre_shared_key="pre_shared_key_here",
            local_address=["10.0.0.2/24"],
            tag="test-wireguard",
            meta={"mtu": 1420, "keepalive": "25s"},
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "wireguard"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 51820
        assert outbound.private_key == "private_key_here"
        assert outbound.peer_public_key == "peer_public_key_here"
        assert outbound.pre_shared_key == "pre_shared_key_here"
        assert outbound.local_address == ["10.0.0.2/24"]
        assert outbound.tag == "test-wireguard"
        assert outbound.mtu == 1420
        assert outbound.keepalive == "25s"

    def test_convert_tuic_server(self):
        """Test conversion of TUIC server to outbound."""
        server = ParsedServer(
            type="tuic",
            address="1.2.3.4",
            port=443,
            uuid="12345678-1234-1234-1234-123456789012",
            password="test_password",
            tag="test-tuic",
            meta={
                "congestion_control": "bbr",
                "zero_rtt_handshake": True,
                "udp_relay_mode": "native",
                "heartbeat": "10s",
            },
        )

        outbound = convert_parsed_server_to_outbound(server)

        assert outbound is not None
        assert outbound.type == "tuic"
        assert outbound.server == "1.2.3.4"
        assert outbound.server_port == 443
        assert outbound.uuid == "12345678-1234-1234-1234-123456789012"
        assert outbound.password == "test_password"
        assert outbound.tag == "test-tuic"
        assert outbound.congestion_control == "bbr"
        assert outbound.zero_rtt_handshake is True
        assert outbound.udp_relay_mode == "native"
        assert outbound.heartbeat == "10s"

    def test_convert_client_profile_to_inbounds(self):
        """Test conversion of ClientProfile to inbounds."""
        profile = ClientProfile(
            name="test_profile",
            inbounds=[
                InboundProfile(
                    type="socks",
                    listen="127.0.0.1",
                    port=1080,
                    options={
                        "tag": "socks-in",
                        "users": [{"username": "user", "password": "pass"}],
                    },
                ),
                InboundProfile(
                    type="http",
                    listen="127.0.0.1",
                    port=8080,
                    options={"tag": "http-in"},
                ),
            ],
        )

        inbounds = convert_client_profile_to_inbounds(profile)

        assert len(inbounds) == 2

        # Check SOCKS inbound
        socks_inbound = inbounds[0]
        assert socks_inbound.type == "socks"
        assert socks_inbound.listen == "127.0.0.1"
        assert socks_inbound.listen_port == 1080
        assert socks_inbound.tag == "socks-in"
        # Note: users are not converted from options in current implementation

        # Check HTTP inbound
        http_inbound = inbounds[1]
        assert http_inbound.type == "http"
        assert http_inbound.listen == "127.0.0.1"
        assert http_inbound.listen_port == 8080
        assert http_inbound.tag == "http-in"

    def test_export_full_configuration(self):
        """Test full configuration export."""
        exporter = SingboxExporterV2()

        # Create test servers
        servers = [
            ParsedServer(
                type="ss",
                address="1.2.3.4",
                port=8388,
                password="test_password",
                security="aes-256-gcm",
                tag="ss-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=443,
                uuid="12345678-1234-1234-1234-123456789012",
                tag="vmess-server",
                meta={"servername": "example.com"},
            ),
        ]

        # Create client profile
        client_profile = ClientProfile(
            name="test_profile",
            inbounds=[
                InboundProfile(
                    type="socks",
                    listen="127.0.0.1",
                    port=1080,
                    options={"tag": "socks-in"},
                )
            ],
        )

        # Export configuration
        config_str = exporter.export(servers, client_profile)
        config = json.loads(config_str)

        # Verify structure
        assert "log" in config
        assert "inbounds" in config
        assert "outbounds" in config
        assert "route" in config

        # Verify inbounds
        assert len(config["inbounds"]) == 1
        assert config["inbounds"][0]["type"] == "socks"
        assert config["inbounds"][0]["listen"] == "127.0.0.1"
        assert config["inbounds"][0]["listen_port"] == 1080

        # Verify outbounds (including default ones)
        assert len(config["outbounds"]) == 5  # urltest + 2 servers + direct + block
        outbound_types = [o["type"] for o in config["outbounds"]]
        assert "shadowsocks" in outbound_types
        assert "vmess" in outbound_types
        assert "direct" in outbound_types
        assert "block" in outbound_types

        # Verify route
        assert config["route"]["final"] == "auto"
        assert len(config["route"]["rules"]) == 3

    def test_export_without_client_profile(self):
        """Test export without client profile."""
        exporter = SingboxExporterV2()

        servers = [
            ParsedServer(
                type="ss",
                address="1.2.3.4",
                port=8388,
                password="test_password",
                security="aes-256-gcm",
                tag="ss-server",
            )
        ]

        config_str = exporter.export(servers)
        config = json.loads(config_str)

        # Should not have inbounds when no client profile
        assert "inbounds" not in config

        # Should have outbounds
        assert len(config["outbounds"]) == 4  # urltest + 1 сервер + direct + block

    def test_export_invalid_server(self):
        """Test export with invalid server data."""
        exporter = SingboxExporterV2()

        # Server without required fields
        servers = [
            ParsedServer(
                type="ss",
                address="1.2.3.4",
                port=8388,
                # Missing password and security
                tag="invalid-ss",
            )
        ]

        # Should not raise exception, but skip invalid server
        config_str = exporter.export(servers)
        config = json.loads(config_str)

        # Should only have default outbounds
        assert len(config["outbounds"]) == 2  # direct + block
        outbound_types = [o["type"] for o in config["outbounds"]]
        assert "direct" in outbound_types
        assert "block" in outbound_types
        assert "shadowsocks" not in outbound_types

    def test_export_unsupported_protocol(self):
        """Test export with unsupported protocol."""
        exporter = SingboxExporterV2()

        servers = [
            ParsedServer(
                type="unsupported",
                address="1.2.3.4",
                port=8388,
                tag="unsupported-server",
            )
        ]

        # Should not raise exception, but skip unsupported protocol
        config_str = exporter.export(servers)
        config = json.loads(config_str)

        # Should only have default outbounds
        assert len(config["outbounds"]) == 2  # direct + block
