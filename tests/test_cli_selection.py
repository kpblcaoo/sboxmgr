import os
import shutil
import pytest
from dotenv import load_dotenv
from conftest import run_cli
import json
from typer.testing import CliRunner
from sboxmgr.cli.main import app

load_dotenv()

runner = CliRunner()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_SRC = os.path.join(PROJECT_ROOT, "config.template.json")

def test_excluded_index(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    monkeypatch.setenv("SBOXMGR_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setenv("SBOXMGR_LOG_FILE", str(tmp_path / "log.txt"))
    # Копируем шаблон в tmp_path
    template_path = tmp_path / "config.template.json"
    shutil.copyfile(TEMPLATE_SRC, template_path)
    monkeypatch.setenv("SBOXMGR_TEMPLATE_FILE", str(template_path))
    runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    result = runner.invoke(app, ["run", "--index", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    output = (result.stdout or "") + (result.stderr or "")
    assert "excluded" in output or "исключён" in output or "Ошибка" in output

def test_excluded_remarks(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    monkeypatch.setenv("SBOXMGR_CONFIG_FILE", str(tmp_path / "config.json"))
    monkeypatch.setenv("SBOXMGR_LOG_FILE", str(tmp_path / "log.txt"))
    template_path = tmp_path / "config.template.json"
    shutil.copyfile(TEMPLATE_SRC, template_path)
    monkeypatch.setenv("SBOXMGR_TEMPLATE_FILE", str(template_path))
    runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    result = runner.invoke(app, ["run", "--remarks", "[NL-2]  vless-reality", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    output = (result.stdout or "") + (result.stderr or "")
    assert "excluded" in output or "исключён" in output or "Ошибка" in output 