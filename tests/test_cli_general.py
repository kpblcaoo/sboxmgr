from conftest import run_cli
import os
import json

def test_dry_run_no_selected_config():
    run_cli(["--index", "1", "-u", "https://example.com/sub-link", "--dry-run"])
    assert not os.path.exists("selected_config.json")

def test_normal_run_creates_selected_config():
    run_cli(["--index", "1", "-u", "https://example.com/sub-link"])
    assert os.path.exists("selected_config.json")
    with open("selected_config.json") as f:
        data = json.load(f)
    assert "selected" in data 