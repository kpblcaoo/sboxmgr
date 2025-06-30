"""CLI tests for export command with Phase 4 enhancements."""

import pytest
import tempfile
import json
import os
from unittest.mock import patch, Mock
from typer.testing import CliRunner

from sboxmgr.cli.commands.export import app


@pytest.fixture
def runner():
    """Create CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def sample_profile():
    """Create sample profile for testing."""
    return {
        "id": "test-profile",
        "description": "Test profile",
        "filters": {"exclude_tags": [], "only_tags": [], "exclusions": [], "only_enabled": True},
        "export": {"format": "sing-box", "outbound_profile": "vless-real", "inbound_profile": "tun", "output_file": "config.json"},
        "metadata": {}
    }

def _contains_any(text, substrings):
    text = text.lower()
    return any(s.lower() in text for s in substrings)

def test_export_dry_run_success(runner):
    """Test export with --dry-run flag."""
    with patch('sboxmgr.cli.commands.export._generate_config_from_subscription') as mock_gen:
        mock_gen.return_value = {"outbounds": [{"type": "direct"}], "route": {"rules": []}}
        result = runner.invoke(app, ["-u", "https://example.com/sub", "--dry-run", "--skip-version-check"])
        assert result.exit_code == 0
        assert _contains_any(result.stdout, ["dry run", "试运行", "проверка", "valid", "有效", "корректен"])

def test_export_agent_check_success(runner):
    """Test export with --agent-check flag."""
    with patch('sboxmgr.cli.commands.export._generate_config_from_subscription') as mock_gen:
        mock_gen.return_value = {"outbounds": [{"type": "direct"}], "route": {"rules": []}}
        with patch('sboxmgr.cli.commands.export._run_agent_check') as mock_check:
            mock_check.return_value = True
            result = runner.invoke(app, ["-u", "https://example.com/sub", "--agent-check", "--skip-version-check"])
            assert result.exit_code == 0
            assert _contains_any(result.stdout, ["agent", "sboxagent", "агент"])

def test_export_validate_only_success(runner):
    """Test export with --validate-only flag."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(json.dumps({"outbounds": [], "route": {"rules": []}}))
        temp_path = f.name
    try:
        with patch('sboxmgr.config.validation.validate_config_file'):
            result = runner.invoke(app, ["--validate-only", "--output", temp_path])
            assert result.exit_code == 0
            assert _contains_any(result.stdout, ["valid", "有效", "корректен"])
    finally:
        os.unlink(temp_path)

def test_export_with_postprocessors_success(runner):
    """Test export with --postprocessors flag."""
    with patch('sboxmgr.cli.commands.export._generate_config_from_subscription') as mock_gen:
        mock_gen.return_value = {"outbounds": [{"type": "direct"}], "route": {"rules": []}}
        result = runner.invoke(app, ["-u", "https://example.com/sub", "--postprocessors", "geo_filter,tag_filter", "--skip-version-check"])
        assert result.exit_code == 0
        assert _contains_any(result.stdout, ["geo_filter", "tag_filter", "постпроцессор", "postprocessor"])

def test_export_with_invalid_postprocessors_error(runner):
    """Test export with invalid postprocessors."""
    result = runner.invoke(app, ["-u", "https://example.com/sub", "--postprocessors", "invalid_processor", "--skip-version-check"])
    assert result.exit_code == 1
    assert _contains_any(result.stderr, ["Unknown postprocessors", "Неизвестные постпроцессоры", "postprocessors"])

def test_export_with_middleware_success(runner):
    """Test export with --middleware flag."""
    with patch('sboxmgr.cli.commands.export._generate_config_from_subscription') as mock_gen:
        mock_gen.return_value = {"outbounds": [{"type": "direct"}], "route": {"rules": []}}
        result = runner.invoke(app, ["-u", "https://example.com/sub", "--middleware", "logging,enrichment", "--skip-version-check"])
        assert result.exit_code == 0
        assert _contains_any(result.stdout, ["middleware", "logging", "enrichment", "middleware"])

def test_export_with_invalid_middleware_error(runner):
    """Test export with invalid middleware."""
    result = runner.invoke(app, ["-u", "https://example.com/sub", "--middleware", "invalid_mw", "--skip-version-check"])
    assert result.exit_code == 1
    assert _contains_any(result.stderr, ["Unknown middleware", "Неизвестное middleware", "middleware"])

def test_export_with_profile_success(runner, sample_profile):
    """Test export with --profile flag."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_profile, f)
        profile_path = f.name
    try:
        with patch('sboxmgr.cli.commands.export._generate_config_from_subscription') as mock_gen:
            mock_gen.return_value = {"outbounds": [{"type": "direct"}], "route": {"rules": []}}
            result = runner.invoke(app, ["-u", "https://example.com/sub", "--profile", profile_path, "--skip-version-check"])
            assert result.exit_code == 0
            assert _contains_any(result.stdout, [
                "profile loaded", "профиль загружен", "profile successfully loaded", "profile успешно загружен"
            ])
    finally:
        os.unlink(profile_path)

def test_export_with_invalid_profile_error(runner):
    """Test export with invalid profile file."""
    result = runner.invoke(app, ["-u", "https://example.com/sub", "--profile", "nonexistent.json", "--skip-version-check"])
    assert result.exit_code == 1
    assert _contains_any(result.stderr, [
        "profile file not found", "файл профиля не найден", "profile not found", "профиль не найден"
    ])

def test_export_generate_profile_success(runner):
    """Test export with --generate-profile flag."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        profile_path = f.name
    try:
        result = runner.invoke(app, ["--generate-profile", profile_path, "--postprocessors", "geo_filter,tag_filter", "--middleware", "logging"])
        assert result.exit_code == 0
        assert _contains_any(result.stdout, [
            "profile generated", "профиль создан", "profile успешно создан"
        ])
        assert os.path.exists(profile_path)
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        assert profile_data["id"] == "cli-generated-profile"
        assert "postprocessors" in profile_data["metadata"]
        assert "middleware" in profile_data["metadata"]
    finally:
        if os.path.exists(profile_path):
            os.unlink(profile_path)

def test_export_flag_combinations_error(runner):
    """Test invalid flag combinations."""
    result = runner.invoke(app, ["-u", "https://example.com/sub", "--dry-run", "--agent-check"])
    assert result.exit_code == 1
    assert _contains_any(result.stderr, ["mutually exclusive", "exclusive", "несовместимы"])

def test_export_help_includes_phase4_flags(runner):
    """Test that Phase 4 flags appear in help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--profile" in result.stdout
    assert "--postprocessors" in result.stdout
    assert "--middleware" in result.stdout
    assert "--generate-profile" in result.stdout 