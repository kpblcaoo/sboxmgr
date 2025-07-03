"""CLI tests for profile management commands."""

import sys
from unittest.mock import MagicMock
sys.modules['src.sboxmgr.logging.core'] = MagicMock()

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from src.sboxmgr.profiles import cli

runner = CliRunner()

# Пример валидного профиля
VALID_PROFILE = {
    "id": "test-profile",
    "description": "Test profile for validation",
    "subscriptions": [
        {
            "id": "test-subscription",
            "enabled": True,
            "priority": 1
        }
    ],
    "filters": {
        "exclude_tags": ["slow"],
        "only_tags": ["premium"],
        "exclusions": [],
        "only_enabled": True
    },
    "routing": {
        "by_source": {},
        "default_route": "tunnel",
        "custom_routes": {}
    },
    "export": {
        "format": "sing-box",
        "outbound_profile": "vless-real",
        "inbound_profile": "tun",
        "output_file": "/tmp/test.json"
    },
    "version": "1.0"
}

# Пример профиля с ошибкой (строка вместо списка в filters)
INVALID_PROFILE = {
    "id": "test-profile",
    "description": "Test profile with errors",
    "subscriptions": [
        {
            "id": "test-subscription",
            "enabled": True,
            "priority": 1
        }
    ],
    "filters": {
        "exclude_tags": "slow",  # Ошибка: должно быть списком
        "only_tags": "premium",  # Ошибка: должно быть списком
        "exclusions": [],
        "only_enabled": True
    },
    "routing": {
        "by_source": {},
        "default_route": "tunnel",
        "custom_routes": {}
    },
    "export": {
        "format": "sing-box",
        "outbound_profile": "vless-real",
        "inbound_profile": "tun",
        "output_file": "/tmp/test.json"
    },
    "version": "1.0"
}

# Пример профиля для тестов apply
APPLY_PROFILE = {
    "id": "apply-test",
    "description": "Profile for apply testing",
    "subscriptions": [
        {
            "id": "test-sub",
            "enabled": True,
            "priority": 1
        }
    ],
    "filters": {
        "exclude_tags": ["slow"],
        "only_tags": ["premium"],
        "exclusions": [],
        "only_enabled": True
    },
    "routing": {
        "by_source": {},
        "default_route": "tunnel",
        "custom_routes": {}
    },
    "export": {
        "format": "sing-box",
        "outbound_profile": "vless-real",
        "inbound_profile": "tun",
        "output_file": "/tmp/apply-test.json"
    },
    "version": "1.0"
}

# Пример второго профиля для тестов diff
DIFF_PROFILE = {
    "id": "diff-test",
    "description": "Profile for diff testing",
    "subscriptions": [
        {
            "id": "diff-sub",
            "enabled": False,
            "priority": 2
        }
    ],
    "filters": {
        "exclude_tags": ["unstable"],
        "only_tags": ["fast"],
        "exclusions": ["blocked"],
        "only_enabled": False
    },
    "routing": {
        "by_source": {},
        "default_route": "direct",
        "custom_routes": {}
    },
    "export": {
        "format": "clash",
        "outbound_profile": "clash-real",
        "inbound_profile": "http",
        "output_file": "/tmp/diff-test.yaml"
    },
    "version": "1.0"
}

def write_profile(tmp_path, data, filename="profile.json"):
    path = tmp_path / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return str(path)


def _contains_any(text, substrings):
    text = text.lower()
    return any(s.lower() in text for s in substrings)


def test_profile_info_valid(tmp_path):
    path = write_profile(tmp_path, VALID_PROFILE)
    result = runner.invoke(cli.app, ["info", path])
    assert result.exit_code == 0
    assert _contains_any(result.output, ["profile info", "информация о профиле"])
    assert _contains_any(result.output, ["valid", "корректен", "валиден", "✓"])
    assert "test.json" in result.output or "profile.json" in result.output


def test_profile_info_invalid(tmp_path):
    broken = {"subscription": {"sources": []}}
    path = write_profile(tmp_path, broken)
    result = runner.invoke(cli.app, ["info", path])
    assert result.exit_code == 0
    assert _contains_any(result.output, ["invalid", "ошибка", "✗"])
    assert _contains_any(result.output, ["error", "ошибка"])


def test_profile_validate_valid(tmp_path):
    path = write_profile(tmp_path, VALID_PROFILE)
    result = runner.invoke(cli.app, ["validate", path])
    assert result.exit_code == 0
    assert _contains_any(result.output, ["profile is valid", "профиль корректен", "валиден"])


def test_profile_validate_invalid(tmp_path):
    path = write_profile(tmp_path, INVALID_PROFILE)
    result = runner.invoke(cli.app, ["validate", path])
    assert result.exit_code != 0
    assert _contains_any(result.output, ["profile validation failed", "ошибка валидации профиля", "ошибка", "failed"])
    assert _contains_any(result.output, ["must be a list", "должен быть списком"])


def test_profile_validate_normalize(tmp_path):
    path = write_profile(tmp_path, INVALID_PROFILE)
    result = runner.invoke(cli.app, ["validate", path, "--normalize"])
    assert result.exit_code == 0
    assert _contains_any(result.output, ["normalized", "нормализован"])
    assert _contains_any(result.output, ["profile is valid", "профиль корректен", "валиден"])


def test_profile_apply_valid(tmp_path):
    """Test profile apply with valid profile."""
    path = write_profile(tmp_path, APPLY_PROFILE)
    result = runner.invoke(cli.app, ["apply", path])
    assert result.exit_code == 0
    assert _contains_any(result.output, ["applied successfully", "успешно применён", "успешно применен"])
    assert "apply-test" in result.output


def test_profile_apply_dry_run(tmp_path):
    """Test profile apply with dry-run flag."""
    path = write_profile(tmp_path, APPLY_PROFILE)
    result = runner.invoke(cli.app, ["apply", path, "--dry-run"])
    assert result.exit_code == 0
    assert "Profile would be applied (dry run)" in result.output
    assert "apply-test" in result.output


def test_profile_apply_invalid(tmp_path):
    """Test profile apply with invalid profile."""
    path = write_profile(tmp_path, INVALID_PROFILE)
    result = runner.invoke(cli.app, ["apply", path])
    assert result.exit_code == 1
    assert "Profile structure validation failed" in result.output


def test_profile_explain_valid(tmp_path):
    """Test profile explain with valid profile."""
    path = write_profile(tmp_path, VALID_PROFILE)
    result = runner.invoke(cli.app, ["explain", path])
    assert result.exit_code == 0
    assert "Profile Explanation" in result.output
    assert "test-profile" in result.output
    assert "Subscriptions" in result.output
    assert "Export" in result.output
    assert "Filters" in result.output


def test_profile_explain_invalid(tmp_path):
    """Test profile explain with invalid profile."""
    path = write_profile(tmp_path, INVALID_PROFILE)
    result = runner.invoke(cli.app, ["explain", path])
    assert result.exit_code == 1
    assert "Failed to explain profile" in result.output


def test_profile_diff_valid(tmp_path):
    """Test profile diff with two valid profiles."""
    path1 = write_profile(tmp_path, VALID_PROFILE, "profile1.json")
    path2 = write_profile(tmp_path, DIFF_PROFILE, "profile2.json")
    result = runner.invoke(cli.app, ["diff", str(path1), str(path2)])
    assert result.exit_code == 0
    assert "Comparing profiles" in result.output
    assert "test-profile" in result.output
    assert "diff-test" in result.output


def test_profile_diff_missing_file(tmp_path):
    """Test profile diff with missing file."""
    path1 = write_profile(tmp_path, VALID_PROFILE, "profile1.json")
    result = runner.invoke(cli.app, ["diff", str(path1), "nonexistent.json"])
    assert result.exit_code == 1
    assert "Profile file not found" in result.output


def test_profile_list_empty(tmp_path):
    """Test profile list with empty directory."""
    # Mock ProfileManager to return empty list
    with patch('src.sboxmgr.profiles.cli.ProfileManager') as mock_manager:
        mock_instance = mock_manager.return_value
        mock_instance.list_profiles.return_value = []
        
        result = runner.invoke(cli.app, ["list"])
        assert result.exit_code == 0
        assert "No profiles found" in result.output


def test_profile_list_with_profiles(tmp_path):
    """Test profile list with profiles."""
    # Mock ProfileManager to return profiles
    from src.sboxmgr.profiles.manager import ProfileInfo
    from datetime import datetime
    
    mock_profiles = [
        ProfileInfo(
            path="/tmp/profile1.json",
            name="profile1",
            size=1024,
            modified=datetime.now(),
            valid=True
        ),
        ProfileInfo(
            path="/tmp/profile2.json", 
            name="profile2",
            size=2048,
            modified=datetime.now(),
            valid=False,
            error="Invalid format"
        )
    ]
    
    with patch('src.sboxmgr.profiles.cli.ProfileManager') as mock_manager:
        mock_instance = mock_manager.return_value
        mock_instance.list_profiles.return_value = mock_profiles
        
        result = runner.invoke(cli.app, ["list"])
        assert result.exit_code == 0
        assert "profile1" in result.output
        assert "profile2" in result.output
        assert "✓ Valid" in result.output
        assert "✗ Invalid" in result.output


def test_profile_switch_valid(tmp_path):
    """Test profile switch with valid profile."""
    # Mock ProfileManager and ProfileLoader
    with patch('src.sboxmgr.profiles.cli.ProfileManager') as mock_manager, \
         patch('src.sboxmgr.profiles.cli.ProfileLoader') as mock_loader:
        
        # Mock ProfileManager
        mock_manager_instance = mock_manager.return_value
        mock_manager_instance.list_profiles.return_value = []
        
        # Mock ProfileLoader
        mock_loader_instance = mock_loader.return_value
        mock_profile = type('MockProfile', (), {
            'id': 'test-profile',
            'description': 'Test profile'
        })()
        mock_loader_instance.load_from_file.return_value = mock_profile
        
        result = runner.invoke(cli.app, ["switch", "test-profile"])
        assert result.exit_code == 0
        assert "Switched to profile" in result.output
        assert "test-profile" in result.output


def test_profile_switch_invalid(tmp_path):
    """Test profile switch with invalid profile."""
    # Mock ProfileManager to raise exception
    with patch('src.sboxmgr.profiles.cli.ProfileManager') as mock_manager:
        mock_instance = mock_manager.return_value
        mock_instance.load_profile.side_effect = FileNotFoundError("Profile not found")
        
        result = runner.invoke(cli.app, ["switch", "nonexistent"])
        assert result.exit_code == 1
        assert "Profile not found" in result.output 