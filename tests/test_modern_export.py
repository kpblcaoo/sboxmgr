"""Tests for modern sing-box export without legacy special outbounds."""

import json

import pytest

from src.sboxmgr.subscription.exporters.singbox_exporter import singbox_export
from src.sboxmgr.subscription.models import ParsedServer


class TestModernExport:
    """Test modern export functionality."""

    def test_modern_export_no_legacy_outbounds(self):
        """Test that modern export doesn't include legacy special outbounds."""
        # Create a simple test server
        server = ParsedServer(
            type="vless",
            address="1.2.3.4",
            port=443,
            uuid="test-uuid",
            tag="test-server",
        )

        # Export using modern function
        config = singbox_export([server])

        # Check that config has outbounds
        assert "outbounds" in config
        assert "route" in config

        # Check that we have the test server
        outbounds = config["outbounds"]
        assert len(outbounds) >= 1

        # Find our test server
        test_outbound = None
        for outbound in outbounds:
            if outbound.get("tag") == "test-server":
                test_outbound = outbound
                break

        assert test_outbound is not None
        assert test_outbound["type"] == "vless"
        assert test_outbound["server"] == "1.2.3.4"
        assert test_outbound["server_port"] == 443

        # Check that we have urltest outbound
        urltest_outbound = None
        for outbound in outbounds:
            if outbound.get("type") == "urltest":
                urltest_outbound = outbound
                break

        assert urltest_outbound is not None
        assert urltest_outbound["tag"] == "auto"
        assert "test-server" in urltest_outbound["outbounds"]

        # Check routing rules
        route = config["route"]
        assert "rules" in route
        assert "final" in route
        assert route["final"] == "auto"

        # Check that rules use actions instead of outbound references
        rules = route["rules"]
        assert len(rules) >= 1

        # Should have DNS hijack rule
        dns_rule = None
        for rule in rules:
            if rule.get("protocol") == "dns":
                dns_rule = rule
                break

        assert dns_rule is not None
        assert dns_rule.get("action") == "hijack-dns"

        # Should have private IP rule
        private_rule = None
        for rule in rules:
            if rule.get("ip_is_private"):
                private_rule = rule
                break

        assert private_rule is not None
        assert private_rule.get("action") == "auto"

    def test_modern_export_json_serialization(self):
        """Test that modern export produces valid JSON."""
        # Create a simple test server
        server = ParsedServer(
            type="vmess",
            address="5.6.7.8",
            port=1080,
            uuid="test-vmess-uuid",
            tag="test-vmess",
        )

        # Export using modern function
        config = singbox_export([server])

        # Should be serializable to JSON
        try:
            json_str = json.dumps(config, indent=2)
            assert len(json_str) > 0

            # Should be valid JSON
            parsed = json.loads(json_str)
            assert parsed == config

        except Exception as e:
            pytest.fail(f"JSON serialization failed: {e}")

    def test_modern_export_no_warnings(self):
        """Test that modern export doesn't produce deprecation warnings."""
        import warnings

        # Create a simple test server
        server = ParsedServer(
            type="trojan",
            address="9.10.11.12",
            port=443,
            password="test-password",
            tag="test-trojan",
        )

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Export using modern function
            config = singbox_export([server])

            # Check that no deprecation warnings were raised
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert (
                len(deprecation_warnings) == 0
            ), f"Got deprecation warnings: {deprecation_warnings}"

            # Config should still be valid
            assert "outbounds" in config
            assert "route" in config

    def test_legacy_vs_modern_export_comparison(self):
        """Test comparison between legacy and modern export."""
        from sboxmgr.subscription.exporters.singbox_exporter_v2 import SingboxExporterV2

        exporter = SingboxExporterV2()
        assert exporter is not None

    def test_modern_export_singbox_compatibility(self):
        """Test that modern export produces sing-box compatible config without warnings."""
        import os
        import subprocess
        import tempfile

        # Create a simple test server
        server = ParsedServer(
            type="vless",
            address="1.2.3.4",
            port=443,
            uuid="test-uuid",
            tag="test-server",
        )

        # Export using modern function
        config = singbox_export([server])

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f, indent=2)
            config_file = f.name

        try:
            # Check if sing-box binary exists
            singbox_path = "./sing-box-1.11.14-linux-amd64/sing-box"
            print(f"Checking sing-box binary at: {singbox_path}")
            print(f"File exists: {os.path.exists(singbox_path)}")
            if not os.path.exists(singbox_path):
                pytest.skip("sing-box binary not found")

            # Run sing-box check
            result = subprocess.run(
                [singbox_path, "check", "-c", config_file],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should not have legacy special outbounds warning
            output = result.stdout + result.stderr
            assert (
                "legacy special outbounds is deprecated" not in output
            ), f"Modern export should not trigger legacy outbounds warning: {output}"

            # Should exit successfully
            assert result.returncode == 0, f"sing-box check failed: {output}"

        finally:
            # Clean up
            if os.path.exists(config_file):
                os.unlink(config_file)

    def test_override_final_action(self):
        """Test that ClientProfile can override final action in routing."""
        from src.sboxmgr.subscription.models import ClientProfile

        # Create a simple test server
        server = ParsedServer(
            type="vless",
            address="1.2.3.4",
            port=443,
            uuid="test-uuid",
            tag="test-server",
        )

        # Create client profile with custom final action
        client_profile = ClientProfile(routing={"final": "direct"})

        # Export using modern function
        config = singbox_export([server], client_profile=client_profile)

        # Check that final action is overridden
        route = config["route"]
        assert route["final"] == "direct", f"Expected 'direct', got '{route['final']}'"

        # Test with different final action
        client_profile.routing["final"] = "block"
        config = singbox_export([server], client_profile=client_profile)
        assert config["route"]["final"] == "block"

    def test_exclude_outbounds(self):
        """Test that ClientProfile can exclude specific outbound types."""
        from src.sboxmgr.subscription.models import ClientProfile

        # Create multiple test servers with different types
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
            ParsedServer(
                type="trojan",
                address="9.10.11.12",
                port=443,
                password="test-pass",
                tag="trojan-server",
            ),
        ]

        # Create client profile that excludes vmess
        client_profile = ClientProfile(exclude_outbounds=["vmess"])

        # Export using modern function
        config = singbox_export(servers, client_profile=client_profile)

        # Check that vmess is excluded
        outbounds = config["outbounds"]
        outbound_types = [o.get("type") for o in outbounds]

        assert "vless" in outbound_types, "vless should be included"
        assert "vmess" not in outbound_types, "vmess should be excluded"
        assert "trojan" in outbound_types, "trojan should be included"

        # Check that urltest outbounds list is updated correctly
        urltest_outbound = None
        for outbound in outbounds:
            if outbound.get("type") == "urltest":
                urltest_outbound = outbound
                break

        assert urltest_outbound is not None, "Should have urltest outbound"
        assert (
            "vless-server" in urltest_outbound["outbounds"]
        ), "urltest should include vless"
        assert (
            "vmess-server" not in urltest_outbound["outbounds"]
        ), "urltest should not include vmess"
        assert (
            "trojan-server" in urltest_outbound["outbounds"]
        ), "urltest should include trojan"

    def test_exclude_multiple_outbounds(self):
        """Test excluding multiple outbound types."""
        from src.sboxmgr.subscription.models import ClientProfile

        # Create multiple test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
            ParsedServer(
                type="trojan",
                address="9.10.11.12",
                port=443,
                password="test-pass",
                tag="trojan-server",
            ),
            ParsedServer(
                type="shadowsocks",
                address="13.14.15.16",
                port=8388,
                password="test-pass",
                tag="ss-server",
            ),
        ]

        # Create client profile that excludes multiple types
        client_profile = ClientProfile(exclude_outbounds=["vmess", "shadowsocks"])

        # Export using modern function
        config = singbox_export(servers, client_profile=client_profile)

        # Check that excluded types are not present
        outbounds = config["outbounds"]
        outbound_types = [o.get("type") for o in outbounds]

        assert "vless" in outbound_types, "vless should be included"
        assert "trojan" in outbound_types, "trojan should be included"
        assert "vmess" not in outbound_types, "vmess should be excluded"
        assert "shadowsocks" not in outbound_types, "shadowsocks should be excluded"

    def test_combined_features(self):
        """Test combining override final action and exclude outbounds."""
        from src.sboxmgr.subscription.models import ClientProfile

        # Create test servers
        servers = [
            ParsedServer(
                type="vless",
                address="1.2.3.4",
                port=443,
                uuid="test-uuid",
                tag="vless-server",
            ),
            ParsedServer(
                type="vmess",
                address="5.6.7.8",
                port=1080,
                uuid="test-vmess-uuid",
                tag="vmess-server",
            ),
        ]

        # Create client profile with both features
        client_profile = ClientProfile(
            routing={"final": "block"}, exclude_outbounds=["vmess"]
        )

        # Export using modern function
        config = singbox_export(servers, client_profile=client_profile)

        # Check both features work together
        route = config["route"]
        assert route["final"] == "block", "Final action should be overridden"

        outbounds = config["outbounds"]
        outbound_types = [o.get("type") for o in outbounds]
        assert "vless" in outbound_types, "vless should be included"
        assert "vmess" not in outbound_types, "vmess should be excluded"
