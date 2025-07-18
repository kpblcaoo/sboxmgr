"""Tests for global flags functionality in CLI."""

import re
import pytest
from typer.testing import CliRunner

from sboxmgr.cli.main import app

# Semantic version pattern for testing
SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-?[\w\.-]+)?(?:\+[\w\.-]+)?$"


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_global_yes_flag(runner):
    """Test that --yes flag is available globally."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--yes" in result.stdout
    assert "-y" in result.stdout
    assert "Skip confirmation prompts" in result.stdout


def test_global_verbose_flag(runner):
    """Test that --verbose flag is available globally."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.stdout
    assert "-v" in result.stdout
    assert "Verbose output" in result.stdout


def test_global_version_flag(runner):
    """Test that --version flag works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    # Should output version or "unknown"
    version_output = result.stdout.strip()
    # Validate version output against semantic versioning or "unknown"
    assert version_output == "unknown" or re.match(SEMVER_PATTERN, version_output)


def test_deprecated_aliases_exist(runner):
    """Test that deprecated command aliases exist."""
    # Test list-servers alias
    result = runner.invoke(app, ["list-servers", "--help"])
    assert result.exit_code == 0

    # Test exclusions alias
    result = runner.invoke(app, ["exclusions", "--help"])
    assert result.exit_code == 0


def test_deprecated_aliases_show_warning(runner):
    """Test that deprecated aliases show warning messages."""
    # Test that deprecated commands show warnings when used
    # We'll use a mock URL to trigger the warning
    result = runner.invoke(app, ["list-servers", "--url", "https://example.com", "--debug", "0"])
    # Should show deprecation warning (exit code 1 due to invalid URL, but warning should appear)
    assert "Warning: 'list-servers' is deprecated" in result.stdout
    # Note: exit code may vary depending on URL processing

    result = runner.invoke(app, ["exclusions", "--url", "https://example.com", "--view"])
    # Should show deprecation warning
    assert "Warning: 'exclusions' is deprecated" in result.stdout
    # Note: exit code may vary depending on URL processing


def test_global_flags_in_context(runner):
    """Test that global flags are passed to context."""
    # This is a basic test - in real usage, we'd need to test with actual commands
    result = runner.invoke(app, ["--yes", "--verbose", "--help"])
    assert result.exit_code == 0
    assert "--yes" in result.stdout
    assert "--verbose" in result.stdout
