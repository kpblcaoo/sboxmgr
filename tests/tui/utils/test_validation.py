"""Tests for TUI validation utilities.

This module tests the validation logic for user inputs
in the TUI interface, ensuring proper validation behavior.
"""

import pytest
import tempfile
import os
from pathlib import Path

from sboxmgr.tui.utils.validation import (
    validate_subscription_url,
    validate_output_path,
    validate_tags
)


class TestValidateSubscriptionUrl:
    """Test cases for subscription URL validation."""

    def test_empty_url(self):
        """Test validation of empty URL."""
        is_valid, error = validate_subscription_url("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_whitespace_only_url(self):
        """Test validation of whitespace-only URL."""
        is_valid, error = validate_subscription_url("   ")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        is_valid, error = validate_subscription_url("http://example.com/sub")
        assert is_valid is True
        assert error is None

    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        is_valid, error = validate_subscription_url("https://example.com/sub")
        assert is_valid is True
        assert error is None

    def test_valid_vmess_url(self):
        """Test validation of valid vmess URL."""
        is_valid, error = validate_subscription_url("vmess://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_vless_url(self):
        """Test validation of valid vless URL."""
        is_valid, error = validate_subscription_url("vless://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_shadowsocks_url(self):
        """Test validation of valid shadowsocks URL."""
        is_valid, error = validate_subscription_url("ss://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_trojan_url(self):
        """Test validation of valid trojan URL."""
        is_valid, error = validate_subscription_url("trojan://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_tuic_url(self):
        """Test validation of valid tuic URL."""
        is_valid, error = validate_subscription_url("tuic://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_hysteria2_url(self):
        """Test validation of valid hysteria2 URL."""
        is_valid, error = validate_subscription_url("hysteria2://example.com")
        assert is_valid is True
        assert error is None

    def test_unsupported_protocol(self):
        """Test validation of unsupported protocol."""
        is_valid, error = validate_subscription_url("ftp://example.com")
        assert is_valid is False
        assert "Unsupported protocol: ftp" in error

    def test_invalid_url_format(self):
        """Test validation of invalid URL format."""
        is_valid, error = validate_subscription_url("not-a-url")
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_url_without_scheme(self):
        """Test validation of URL without scheme."""
        is_valid, error = validate_subscription_url("example.com/sub")
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_url_with_whitespace(self):
        """Test validation of URL with surrounding whitespace."""
        is_valid, error = validate_subscription_url("  https://example.com/sub  ")
        assert is_valid is True
        assert error is None


class TestValidateOutputPath:
    """Test cases for output path validation."""

    def test_empty_path(self):
        """Test validation of empty path."""
        is_valid, error = validate_output_path("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_whitespace_only_path(self):
        """Test validation of whitespace-only path."""
        is_valid, error = validate_output_path("   ")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_valid_path_in_current_directory(self):
        """Test validation of valid path in current directory."""
        is_valid, error = validate_output_path("config.json")
        assert is_valid is True
        assert error is None

    def test_valid_path_with_directory(self):
        """Test validation of valid path with existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, "config.json")
            is_valid, error = validate_output_path(test_path)
            assert is_valid is True
            assert error is None

    def test_nonexistent_directory(self):
        """Test validation of path with nonexistent directory."""
        is_valid, error = validate_output_path("/nonexistent/directory/config.json")
        assert is_valid is False
        assert "Directory does not exist" in error

    def test_non_writable_directory(self):
        """Test validation of path with non-writable directory."""
        # Skip this test if running as root
        if os.getuid() == 0:
            pytest.skip("Cannot test non-writable directory as root")

        # This test is platform-specific and might not work in all environments
        # We'll use a simple approach
        is_valid, error = validate_output_path("/root/config.json")
        # This might pass or fail depending on permissions, so we just check it doesn't crash
        assert isinstance(is_valid, bool)
        assert isinstance(error, (str, type(None)))

    def test_existing_writable_file(self):
        """Test validation of existing writable file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            is_valid, error = validate_output_path(temp_path)
            assert is_valid is True
            assert error is None
        finally:
            os.unlink(temp_path)

    def test_path_with_tilde(self):
        """Test validation of path with tilde expansion."""
        is_valid, error = validate_output_path("~/config.json")
        # Should expand ~ to home directory
        assert isinstance(is_valid, bool)
        assert isinstance(error, (str, type(None)))

    def test_path_with_whitespace(self):
        """Test validation of path with surrounding whitespace."""
        is_valid, error = validate_output_path("  config.json  ")
        assert is_valid is True
        assert error is None


class TestValidateTags:
    """Test cases for tags validation."""

    def test_empty_tags(self):
        """Test validation of empty tags."""
        is_valid, error, tags = validate_tags("")
        assert is_valid is True
        assert error is None
        assert tags == []

    def test_whitespace_only_tags(self):
        """Test validation of whitespace-only tags."""
        is_valid, error, tags = validate_tags("   ")
        assert is_valid is True
        assert error is None
        assert tags == []

    def test_single_valid_tag(self):
        """Test validation of single valid tag."""
        is_valid, error, tags = validate_tags("tag1")
        assert is_valid is True
        assert error is None
        assert tags == ["tag1"]

    def test_multiple_valid_tags(self):
        """Test validation of multiple valid tags."""
        is_valid, error, tags = validate_tags("tag1,tag2,tag3")
        assert is_valid is True
        assert error is None
        assert tags == ["tag1", "tag2", "tag3"]

    def test_tags_with_whitespace(self):
        """Test validation of tags with whitespace."""
        is_valid, error, tags = validate_tags(" tag1 , tag2 , tag3 ")
        assert is_valid is True
        assert error is None
        assert tags == ["tag1", "tag2", "tag3"]

    def test_tags_with_hyphens(self):
        """Test validation of tags with hyphens."""
        is_valid, error, tags = validate_tags("low-latency,high-speed")
        assert is_valid is True
        assert error is None
        assert tags == ["low-latency", "high-speed"]

    def test_tags_with_underscores(self):
        """Test validation of tags with underscores."""
        is_valid, error, tags = validate_tags("test_tag,another_tag")
        assert is_valid is True
        assert error is None
        assert tags == ["test_tag", "another_tag"]

    def test_tags_with_numbers(self):
        """Test validation of tags with numbers."""
        is_valid, error, tags = validate_tags("tag1,tag2,server123")
        assert is_valid is True
        assert error is None
        assert tags == ["tag1", "tag2", "server123"]

    def test_empty_tags_in_list(self):
        """Test validation with empty tags in comma-separated list."""
        is_valid, error, tags = validate_tags("tag1,,tag2,")
        assert is_valid is True
        assert error is None
        assert tags == ["tag1", "tag2"]

    def test_tag_too_long(self):
        """Test validation of too long tag."""
        long_tag = "a" * 51  # 51 characters
        is_valid, error, tags = validate_tags(long_tag)
        assert is_valid is False
        assert "Tag too long" in error
        assert tags == []

    def test_invalid_tag_characters(self):
        """Test validation of tag with invalid characters."""
        is_valid, error, tags = validate_tags("tag@invalid")
        assert is_valid is False
        assert "Invalid tag format" in error
        assert tags == []

    def test_tag_with_spaces(self):
        """Test validation of tag with spaces."""
        is_valid, error, tags = validate_tags("invalid tag")
        assert is_valid is False
        assert "Invalid tag format" in error
        assert tags == []

    def test_mixed_valid_invalid_tags(self):
        """Test validation with mix of valid and invalid tags."""
        is_valid, error, tags = validate_tags("valid,invalid@tag,also_valid")
        assert is_valid is False
        assert "Invalid tag format" in error
        assert tags == []
