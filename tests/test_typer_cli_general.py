import pytest
from typer.testing import CliRunner
from sboxmgr.cli.main import app
import os
import json

runner = CliRunner()

@pytest.fixture
def fake_url():
    return "https://example.com/sub-link"

@pytest.fixture
def minimal_config():
    # Минимальный валидный конфиг для fetch_json
    return {
        "outbounds": [
            {"type": "vless", "tag": "proxy-1", "server": "1.2.3.4", "server_port": 443, "uuid": "abc"}
        ]
    }

@pytest.fixture
def patch_fetch_json(monkeypatch, minimal_config):
    monkeypatch.setattr("sboxmgr.cli.main.fetch_json", lambda url: minimal_config)


def test_run_creates_selected_config(tmp_path, monkeypatch, fake_url, patch_fetch_json):
    # Генерируем минимальный config.template.json
    template_path = tmp_path / "config.template.json"
    template_path.write_text(json.dumps({
        "outbounds": [],
        "route": {"rules": []}
    }))
    monkeypatch.setenv("SBOXMGR_SELECTED_CONFIG_FILE", str(tmp_path / "selected_config.json"))
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    monkeypatch.setenv("SBOXMGR_TEMPLATE_FILE", str(template_path))
    monkeypatch.setenv("SBOXMGR_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setenv("SBOXMGR_BACKUP_FILE", str(tmp_path / "config.json.bak"))
    monkeypatch.setenv("SBOXMGR_URL", fake_url)
    # Пробуем без --url, если не сработает — fallback на --url
    result = runner.invoke(app, ["run", "--index", "0"])
    if result.exit_code != 0:
        # fallback: явно передаём --url
        result = runner.invoke(app, ["run", "--index", "0", "-u", fake_url])
    assert result.exit_code == 0, f"Output: {result.output}\nException: {result.exception}"
    config_path = tmp_path / "selected_config.json"
    assert config_path.exists()
    with open(config_path) as f:
        data = json.load(f)
    assert "selected" in data 