import os
import json
import pytest
from typer.testing import CliRunner
from src.sboxmgr.cli.main import app

runner = CliRunner()

@pytest.mark.usefixtures("cleanup_files")
def test_exclude_and_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    result1 = runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    result2 = runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    exclusions_path = tmp_path / "exclusions.json"
    assert exclusions_path.exists()
    with open(exclusions_path) as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1
    assert "already excluded" in (result2.stdout or "")

@pytest.mark.usefixtures("cleanup_files")
def test_clear_exclusions(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    exclusions_path = tmp_path / "exclusions.json"
    assert exclusions_path.exists()
    runner.invoke(app, ["clear-exclusions", "--yes"])
    if exclusions_path.exists():
        print("exclusions.json after clear:")
        print(exclusions_path.read_text())
    assert not exclusions_path.exists()

@pytest.mark.usefixtures("cleanup_files")
def test_broken_exclusions_json(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    exclusions_path = tmp_path / "exclusions.json"
    with open(exclusions_path, "w") as f:
        f.write("{broken json")
    result = runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "2"])
    assert "повреждён" in (result.stdout or "") or "поврежден" in (result.stdout or "")
    with open(exclusions_path) as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1

@pytest.mark.usefixtures("cleanup_files")
def test_view_exclusions(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_EXCLUSION_FILE", str(tmp_path / "exclusions.json"))
    runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"])
    result = runner.invoke(app, ["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--view"])
    assert "Current Exclusions" in (result.stdout or "") 