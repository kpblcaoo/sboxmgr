import os
from dotenv import load_dotenv
from conftest import run_cli
import json
import pytest

load_dotenv()

@pytest.mark.usefixtures("cleanup_files")
def test_dry_run_no_selected_config(tmp_path):
    run_cli(["run", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"], cwd=tmp_path)
    assert not (tmp_path / "selected_config.json").exists()

@pytest.mark.usefixtures("cleanup_files")
def test_normal_run_creates_selected_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SBOXMGR_SELECTED_CONFIG_FILE", str(tmp_path / "selected_config.json"))
    result = run_cli(["run", "-u", os.getenv("TEST_URL", "https://example.com/sub-link")], cwd=tmp_path)
    config_path = tmp_path / "selected_config.json"
    if not config_path.exists():
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
    assert config_path.exists()
    with open(config_path) as f:
        data = json.load(f)
    assert "selected" in data 