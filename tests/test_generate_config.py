import os
from unittest.mock import patch, mock_open
from update_singbox import generate_config
import pytest

@patch("builtins.open", new_callable=mock_open, read_data='{"type": "template"}')
@patch("os.path.exists", side_effect=lambda x: x == "./config.template.json")
@patch("subprocess.run")
def test_generate_config(mock_subprocess, mock_exists, mock_file):
    outbound = {"type": "vless", "server": "1.1.1.1", "server_port": 443, "uuid": "uuid123"}
    generate_config(outbound)
    mock_file().write.assert_called_once()
    mock_subprocess.assert_called_once_with(["sing-box", "check", "-c", "/etc/sing-box/config.json"], check=True)