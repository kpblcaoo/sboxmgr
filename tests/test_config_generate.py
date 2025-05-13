import pytest
import json
import os
from unittest.mock import patch, mock_open
from modules.config_generate import generate_config

@pytest.fixture
def template_content():
    return {
        "log": {"level": "info"},
        "inbounds": [],
        "outbounds": [
            {
                "type": "urltest",
                "tag": "auto",
                "outbounds": [],
                "url": "https://www.gstatic.com/generate_204",
                "interval": "3m",
                "tolerance": 50,
                "idle_timeout": "30m",
                "interrupt_exist_connections": False
            },
            {"type": "direct", "tag": "direct"}
        ],
        "route": {"rules": [], "final": "auto"},
        "experimental": {"cache_file": {"enabled": True}}
    }

@patch("modules.config_generate.subprocess.run")
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("os.rename")
def test_generate_config(mock_rename, mock_exists, mock_open_file, mock_run, tmp_path, template_content):
    # Mock subprocess.run to simulate successful sing-box check
    mock_run.return_value.returncode = 0

    # Mock os.path.exists to simulate template existence and no existing config
    mock_exists.side_effect = lambda x: x == str(tmp_path / "template.json")

    # Prepare file paths
    template_file = tmp_path / "template.json"
    config_file = tmp_path / "config.json"
    backup_file = tmp_path / "backup.json"
    temp_config_file = tmp_path / "config.json.tmp"

    # Create a single mock_open instance to handle both read and write
    template_data = json.dumps(template_content)
    mock_open_file.return_value.read.return_value = template_data

    # Test data
    outbounds = [
        {"type": "vless", "tag": "proxy-a", "server": "example.com", "server_port": 443, "uuid": "uuid-example"}
    ]

    # Run the function
    result = generate_config(outbounds, str(template_file), str(config_file), str(backup_file))
    assert result is True

    # Check the written config (to temp_config_file)
    # Access the write call from the mock_open_file
    written_data = mock_open_file().write.call_args[0][0]
    written_config = json.loads(written_data)
    assert written_config["outbounds"][1] == outbounds[0]  # Check provider outbound
    assert written_config["outbounds"][0]["outbounds"] == ["proxy-a"]  # Check urltest outbounds

    # Verify rename operations
    mock_rename.assert_any_call(str(temp_config_file), str(config_file))

@patch("modules.config_generate.subprocess.run")
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists")
@patch("os.rename")
def test_generate_config_no_outbounds(mock_rename, mock_exists, mock_open_file, mock_run, tmp_path, template_content):
    # Mock subprocess.run to simulate successful sing-box check
    mock_run.return_value.returncode = 0

    # Mock os.path.exists to simulate template existence and no existing config
    mock_exists.side_effect = lambda x: x == str(tmp_path / "template.json")

    # Prepare file paths
    template_file = tmp_path / "template.json"
    config_file = tmp_path / "config.json"
    backup_file = tmp_path / "backup.json"
    temp_config_file = tmp_path / "config.json.tmp"

    # Create a single mock_open instance to handle both read and write
    template_data = json.dumps(template_content)
    mock_open_file.return_value.read.return_value = template_data

    # Test with empty outbounds
    outbounds = []

    # Run the function
    result = generate_config(outbounds, str(template_file), str(config_file), str(backup_file))
    assert result is True

    # Check the written config
    # Access the write call from the mock_open_file
    written_data = mock_open_file().write.call_args[0][0]
    written_config = json.loads(written_data)
    assert len(written_config["outbounds"]) == 2  # Only urltest and direct
    assert written_config["outbounds"][0]["outbounds"] == []  # Empty urltest outbounds

    # Verify rename operations
    mock_rename.assert_any_call(str(temp_config_file), str(config_file))