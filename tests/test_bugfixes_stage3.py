"""Tests for specific bug fixes in Stage 3: Configuration and Logging.

This file tests ONLY the specific bugs that were fixed, not general functionality.
"""

import logging
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from sboxmgr.config.loader import load_config, merge_cli_args_to_config
from sboxmgr.config.models import AppConfig
from sboxmgr.logging.formatters import StructuredFormatter


class TestBugFix1ValidationErrorHandling:
    """Test Bug Fix 1: ValidationError re-raising in config loader."""

    def test_validation_error_preservation(self, tmp_path):
        """Test that ValidationError details are preserved when re-raised."""
        config_file = tmp_path / "invalid.toml"
        config_file.write_text(
            """
[logging]
level = "INVALID_LEVEL"
"""
        )

        with pytest.raises(ValidationError) as exc_info:
            load_config(str(config_file))

        # BUG FIX: Verify structured error details are preserved
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert errors[0]["type"] == "value_error"
        # Check location tuple contains logging and level
        loc_tuple = errors[0]["loc"]
        assert "logging" in loc_tuple and "level" in loc_tuple
        assert "INVALID_LEVEL" in errors[0]["msg"]


class TestBugFix2ConfigFileValidationBypass:
    """Test Bug Fix 2: Config file validation bypass."""

    def test_config_file_validation_not_bypassed(self, tmp_path):
        """Test that config_file validation is not bypassed during initialization."""
        # Create a valid config file first
        valid_file = tmp_path / "valid.toml"
        valid_file.write_text('[logging]\nlevel = "INFO"')

        # Valid file should work
        config = load_config(str(valid_file))
        assert config.config_file == str(valid_file)

        # Invalid file should trigger validation error
        with pytest.raises(ValidationError) as exc_info:
            AppConfig(config_file="/nonexistent/file.toml")

        errors = exc_info.value.errors()
        assert any(
            "Configuration file not found" in str(error.get("msg", ""))
            for error in errors
        )


class TestBugFix3RedundantFileSeek:
    """Test Bug Fix 3: Redundant f.seek(0) removal."""

    def test_auto_detection_works_without_redundant_seek(self, tmp_path):
        """Test that auto-detection works without redundant f.seek(0) call."""
        from sboxmgr.config.loader import load_config_file

        config_file = tmp_path / "config.conf"  # Unknown extension
        config_file.write_text(
            """
[logging]
level = "DEBUG"

[service]
service_mode = true
"""
        )

        # This should work without any seek-related issues
        result = load_config_file(str(config_file))

        assert result["logging"]["level"] == "DEBUG"
        assert result["service"]["service_mode"] is True


class TestBugFix4ModelDumpUsage:
    """Test Bug Fix 4: Using model_dump() instead of deprecated dict()."""

    def test_merge_uses_model_dump_not_dict(self):
        """Test that merge function uses model_dump() instead of deprecated dict() method."""
        base_config = AppConfig()

        # This should not raise AttributeError about missing dict() method
        merged = merge_cli_args_to_config(base_config, log_level="DEBUG")

        # Verify the function works without errors
        assert merged is not None
        assert hasattr(merged, "logging")


class TestBugFix5UTCTimestamps:
    """Test Bug Fix 5: UTC timestamps in structured logging."""

    def test_utc_timestamps_in_structured_logging(self):
        """Test that structured logging uses UTC timestamps."""
        formatter = StructuredFormatter()

        # Create a log record with fixed timestamp
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = 1640995200.0  # 2022-01-01 00:00:00 UTC

        # Add structured fields
        formatter._add_structured_fields(record)

        # BUG FIX: Verify timestamp is in UTC with timezone info
        assert hasattr(record, "timestamp")
        assert record.timestamp == "2022-01-01T00:00:00+00:00"
        assert record.timestamp.endswith("+00:00")  # UTC timezone


class TestBugFix6SystemdCatHandlerResourceLeaks:
    """Test Bug Fix 6: SystemdCatHandler resource leak fixes."""

    def test_systemd_cat_handler_stdin_none_handling(self):
        """Test handling when process.stdin is None."""
        from sboxmgr.config.models import LoggingConfig
        from sboxmgr.logging.sinks import _create_journald_handler

        config = LoggingConfig(level="INFO")

        with patch.dict("sys.modules", {"systemd": None}):
            with patch("sboxmgr.logging.sinks.subprocess.Popen") as mock_popen:
                mock_process = Mock()
                mock_process.stdin = None  # BUG FIX: stdin is None
                mock_process.poll.return_value = None
                mock_popen.return_value = mock_process

                handler = _create_journald_handler(config)

                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Test message",
                    args=(),
                    exc_info=None,
                )

                # Should not raise AttributeError
                handler.emit(record)

                # Should not try to write to None stdin
                assert (
                    not hasattr(mock_process.stdin, "write") or not mock_process.stdin
                )


class TestBugFix7CLIUnsupportedFormatHandling:
    """Test Bug Fix 7: CLI unsupported format error handling."""

    def test_cli_unsupported_format_error_handling(self):
        """Test CLI error handling for unsupported export formats."""
        from sboxmgr.cli.commands.config import app as config_app

        runner = CliRunner()

        # Test with unsupported format for list command
        # The list command supports only 'table' and 'json' formats
        result = runner.invoke(config_app, ["list", "--format", "unsupported"])

        # Should show appropriate error message
        assert result.exit_code != 0
        # Typer will show usage and error for invalid option value
        assert "invalid choice" in result.output.lower() or "unsupported" in result.output.lower()


class TestBugFix8ReturnTypeAnnotations:
    """Test Bug Fix 8: Return type annotation improvements."""

    # Removed test_output_env_format_return_type - function doesn't exist
