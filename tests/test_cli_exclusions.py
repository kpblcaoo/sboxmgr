import os
import json
from conftest import run_cli
from dotenv import load_dotenv

load_dotenv()

def test_exclude_and_idempotent():
    # 1. Добавить exclusions
    result1 = run_cli(["--exclude", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    # 2. Повторить добавление
    result2 = run_cli(["--exclude", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    # 3. Проверить exclusions.json
    with open("exclusions.json") as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1
    assert "already excluded" in result2.stdout

def test_clear_exclusions():
    run_cli(["--exclude", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    assert os.path.exists("exclusions.json")
    run_cli(["--clear-exclusions"])
    assert not os.path.exists("exclusions.json")

def test_broken_exclusions_json():
    with open("exclusions.json", "w") as f:
        f.write("{broken json")
    result = run_cli(["--exclude", "2", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    assert "повреждён" in result.stdout or "поврежден" in result.stdout
    with open("exclusions.json") as f:
        data = json.load(f)
    assert len(data["exclusions"]) == 1

def test_view_exclusions():
    run_cli(["--exclude", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    result = run_cli(["--exclude", "", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    assert "Current Exclusions" in result.stdout 