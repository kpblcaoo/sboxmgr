import pytest
import subprocess
import os
import json
from update-singbox import fetch_json, validate_server, generate_config

# Mock data for subscription
MOCK_SERVERS = [
    {"type": "vless", "server": "server1.example.com", "port": 443},
    {"type": "vmess", "server": "server2.example.com", "port": 443}
]

MOCK_TEMPLATE = """{
  "log": { "level": "info" },
  "inbounds": [
    { "type": "socks", "tag": "socks-in", "listen": "127.0.0.1", "listen_port": 1080 }
  ],
  "outbounds": [
    $outbound_json,
    { "type": "direct", "tag": "direct" }
  ]
}"""

@pytest.fixture
def mock_template_file(tmp_path):
    """Create a temporary template file."""
    template_file = tmp_path / "config.template.json"
    template_file.write_text(MOCK_TEMPLATE)
    return template_file

@pytest.fixture
def mock_config_file(tmp_path):
    """Path for the generated config file."""
    return tmp_path / "config.json"

def test_fetch_json(mocker):
    """Test fetching JSON data from a URL."""
    mocker.patch("update-singbox.urlopen")
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(MOCK_SERVERS).encode()
    update-singbox.urlopen.return_value = mock_response

    data = fetch_json("https://example.com/subscription")
    assert len(data) == 2
    assert data[0]["server"] == "server1.example.com"

def test_validate_server(mocker):
    """Test server validation using check_availability.py."""
    mocker.patch("subprocess.run")
    subprocess.run.return_value.returncode = 0  # Simulate valid server

    assert validate_server("server1.example.com", 443) is True
    subprocess.run.return_value.returncode = 1  # Simulate invalid server
    assert validate_server("server2.example.com", 443) is False

def test_generate_config(mock_template_file, mock_config_file):
    """Test configuration generation."""
    valid_servers = [
        {"type": "vless", "server": "server1.example.com", "port": 443}
    ]

    # Replace TEMPLATE_FILE and CONFIG_FILE with mocks
    global TEMPLATE_FILE, CONFIG_FILE
    TEMPLATE_FILE = mock_template_file
    CONFIG_FILE = mock_config_file

    generate_config(valid_servers)
    assert CONFIG_FILE.exists()
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        assert config["outbounds"][0]["type"] == "url-test"
        assert config["outbounds"][0]["outbounds"][0]["server"] == "server1.example.com"