import os
import json
from conftest import run_cli
from dotenv import load_dotenv
import pytest

load_dotenv()

@pytest.mark.usefixtures("cleanup_files")
def test_exclude_and_idempotent(tmp_path):
    # 1. Добавить exclusions
    result1 = run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"], cwd=tmp_path)
    # 2. Повторить добавление
    result2 = run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"], cwd=tmp_path)
    # 3. Проверить exclusions.json
    exclusions_path = tmp_path / "exclusions.json"
    assert exclusions_path.exists()
    with open(exclusions_path) as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1
    assert "already excluded" in (result2.stdout or "")

@pytest.mark.usefixtures("cleanup_files")
def test_clear_exclusions(tmp_path):
    run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"], cwd=tmp_path)
    exclusions_path = tmp_path / "exclusions.json"
    assert exclusions_path.exists()
    run_cli(["clear-exclusions", "--yes"], cwd=tmp_path)
    if exclusions_path.exists():
        print("exclusions.json after clear:")
        print(exclusions_path.read_text())
    assert not exclusions_path.exists()

@pytest.mark.usefixtures("cleanup_files")
def test_broken_exclusions_json(tmp_path):
    exclusions_path = tmp_path / "exclusions.json"
    with open(exclusions_path, "w") as f:
        f.write("{broken json")
    result = run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "2"], cwd=tmp_path)
    assert "повреждён" in (result.stdout or "") or "поврежден" in (result.stdout or "")
    with open(exclusions_path) as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1

@pytest.mark.usefixtures("cleanup_files")
def test_view_exclusions(tmp_path):
    run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--add", "1"], cwd=tmp_path)
    result = run_cli(["exclusions", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--view"], cwd=tmp_path)
    assert "Current Exclusions" in (result.stdout or "") 