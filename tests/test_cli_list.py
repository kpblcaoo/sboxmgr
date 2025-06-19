import os
import pytest
from typer.testing import CliRunner
from src.sboxmgr.cli.main import app

runner = CliRunner()

def test_list_servers_excluded(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    monkeypatch.setenv("SBOXMGR_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setenv("SBOXMGR_LOG_FILE", str(tmp_path / "log.txt"))
    runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    result = runner.invoke(app, ["list-servers", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "-d", "2"])
    assert "[excluded]" in result.stdout 