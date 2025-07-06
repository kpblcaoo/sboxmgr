"""Tests for TagNormalizer middleware."""

import pytest
from unittest.mock import Mock

from sboxmgr.subscription.middleware.tag_normalizer import TagNormalizer
from sboxmgr.subscription.models import ParsedServer, PipelineContext


class TestTagNormalizer:
    """Test cases for TagNormalizer middleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = TagNormalizer()
        self.context = PipelineContext(source="test")

    def test_priority_1_name_from_meta(self):
        """Test that meta['name'] has highest priority."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="old-tag",
            meta={"name": "🇳🇱 Netherlands Server", "tag": "nl-server"}
        )

        result = self.normalizer._normalize_tag(server)
        assert result == "🇳🇱 Netherlands Server"

    def test_priority_2_tag_from_meta(self):
        """Test that meta['tag'] has second priority."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="old-tag",
            meta={"tag": "nl-server"}
        )

        result = self.normalizer._normalize_tag(server)
        assert result == "nl-server"

    def test_priority_2_label_from_meta(self):
        """Test that meta['label'] has second priority."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="old-tag",
            meta={"label": "🇨🇦 Canada Server"}
        )

        result = self.normalizer._normalize_tag(server)
        assert result == "🇨🇦 Canada Server"

    def test_priority_3_existing_tag(self):
        """Test that existing tag has third priority."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="existing-tag",
            meta={}
        )

        result = self.normalizer._normalize_tag(server)
        assert result == "existing-tag"

    def test_priority_4_address_fallback(self):
        """Test that address fallback has fourth priority."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="",
            meta={}
        )

        result = self.normalizer._normalize_tag(server)
        assert result == "vless-192.168.1.1"

    def test_priority_5_protocol_fallback(self):
        """Test that protocol fallback has lowest priority."""
        server = ParsedServer(
            type="vless",
            address="",
            port=443,
            tag="",
            meta={}
        )

        result = self.normalizer._normalize_tag(server)
        assert result.startswith("vless-")

    def test_tag_sanitization(self):
        """Test that tags are properly sanitized."""
        test_cases = [
            ("Server with spaces", "Server with spaces"),
            ("Server@#$%^&*()+=", "Server@#$%^&*()+="),  # Keep all printable chars
            ("🇳🇱 Netherlands-1", "🇳🇱 Netherlands-1"),
            ("Server   with   multiple   spaces", "Server with multiple spaces"),
            ("", "unnamed-server"),
            ("   ", "unnamed-server"),
        ]

        for input_tag, expected in test_cases:
            result = self.normalizer._sanitize_tag(input_tag)
            assert result == expected, f"Failed for input: '{input_tag}'"

    def test_unique_tag_generation(self):
        """Test that duplicate tags get unique suffixes."""
        # First tag should be unchanged
        tag1 = self.normalizer._ensure_unique_tag("server")
        assert tag1 == "server"

        # Second identical tag should get suffix
        tag2 = self.normalizer._ensure_unique_tag("server")
        assert tag2 == "server (1)"

        # Third identical tag should get next suffix
        tag3 = self.normalizer._ensure_unique_tag("server")
        assert tag3 == "server (2)"

    def test_process_servers_integration(self):
        """Test full server processing integration."""
        servers = [
            ParsedServer(
                type="vless",
                address="192.168.1.1",
                port=443,
                tag="old-tag",
                meta={"name": "🇳🇱 Netherlands Server"}
            ),
            ParsedServer(
                type="vless",
                address="192.168.1.2",
                port=443,
                tag="old-tag",
                meta={"name": "🇳🇱 Netherlands Server"}  # Duplicate name
            ),
            ParsedServer(
                type="vless",
                address="192.168.1.3",
                port=443,
                tag="unique-tag",
                meta={}
            ),
        ]

        result = self.normalizer.process(servers, self.context)

        # Check that all servers are returned
        assert len(result) == 3

        # Check tag normalization
        assert result[0].tag == "🇳🇱 Netherlands Server"
        assert result[1].tag == "🇳🇱 Netherlands Server (1)"  # Duplicate gets suffix
        assert result[2].tag == "unique-tag"

    def test_empty_servers_list(self):
        """Test handling of empty servers list."""
        result = self.normalizer.process([], self.context)
        assert result == []

    def test_servers_with_no_meta(self):
        """Test handling of servers with no meta field."""
        server = ParsedServer(
            type="vless",
            address="192.168.1.1",
            port=443,
            tag="test-tag",
            meta={}  # Empty dict instead of None
        )

        result = self.normalizer.process([server], self.context)
        assert len(result) == 1
        assert result[0].tag == "test-tag"

    def test_clash_vs_sfi_normalization(self):
        """Test that different User-Agent formats produce consistent results."""
        # Simulate ClashMeta format (with human-readable name)
        clash_server = ParsedServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            tag="vless-192.142.18.243",
            meta={"name": "🇳🇱 kpblcaoo Nederland-3"}
        )

        # Simulate SFI format (IP-based tag)
        sfi_server = ParsedServer(
            type="vless",
            address="192.142.18.243",
            port=443,
            tag="vless-192.142.18.243",
            meta={}
        )

        # Process separately to avoid unique tag conflicts
        normalizer1 = TagNormalizer()
        normalizer2 = TagNormalizer()

        clash_result = normalizer1.process([clash_server], self.context)
        sfi_result = normalizer2.process([sfi_server], self.context)

        # ClashMeta should use human-readable name
        assert clash_result[0].tag == "🇳🇱 kpblcaoo Nederland-3"

        # SFI should use existing tag
        assert sfi_result[0].tag == "vless-192.142.18.243"

    def test_middleware_interface_compliance(self):
        """Test that TagNormalizer complies with middleware interface."""
        # Test can_process
        servers = [ParsedServer(type="vless", address="1.1.1.1", port=443)]
        assert self.normalizer.can_process(servers, self.context) is True

        # Test with empty servers
        assert self.normalizer.can_process([], self.context) is False

        # Test get_metadata
        metadata = self.normalizer.get_metadata()
        assert metadata["name"] == "TagNormalizer"
        assert metadata["type"] == "middleware"
        assert metadata["enabled"] is True

    def test_configuration_handling(self):
        """Test middleware configuration handling."""
        config = {"enabled": False}
        normalizer = TagNormalizer(config)

        assert normalizer.enabled is False
        assert normalizer.config == config

    def test_large_server_list_performance(self):
        """Test performance with large server lists."""
        # Create 100 servers with various tag patterns
        servers = []
        for i in range(100):
            server = ParsedServer(
                type="vless",
                address=f"192.168.1.{i}",
                port=443,
                tag=f"server-{i % 10}",  # Some duplicates
                meta={"name": f"Server {i}"} if i % 2 == 0 else {}
            )
            servers.append(server)

        result = self.normalizer.process(servers, self.context)

        # All servers should be processed
        assert len(result) == 100

        # Tags should be unique
        tags = [server.tag for server in result]
        assert len(set(tags)) == len(tags)

    def test_unicode_tag_handling(self):
        """Test handling of Unicode characters in tags."""
        servers = [
            ParsedServer(
                type="vless",
                address="1.1.1.1",
                port=443,
                meta={"name": "🇺🇸 United States"}
            ),
            ParsedServer(
                type="vless",
                address="2.2.2.2",
                port=443,
                meta={"name": "🇯🇵 日本サーバー"}
            ),
            ParsedServer(
                type="vless",
                address="3.3.3.3",
                port=443,
                meta={"name": "🇷🇺 Российский сервер"}
            ),
        ]

        result = self.normalizer.process(servers, self.context)

        assert result[0].tag == "🇺🇸 United States"
        assert result[1].tag == "🇯🇵 日本サーバー"
        assert result[2].tag == "🇷🇺 Российский сервер"

    def test_flag_emoji_handling(self):
        """Test that flag emojis are preserved correctly."""
        test_cases = [
            "🇳🇱 Netherlands",
            "🇺🇸 USA",
            "🇯🇵 Japan",
            "🇷🇺 Russia",
            "🇨🇦 Canada",
            "🇩🇪 Germany",
            "🇺🇦 Ukraine",
        ]

        for flag_emoji in test_cases:
            sanitized = self.normalizer._sanitize_tag(flag_emoji)
            assert sanitized == flag_emoji, f"Flag emoji '{flag_emoji}' was modified: '{sanitized}'"
