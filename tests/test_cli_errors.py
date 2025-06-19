import os
from dotenv import load_dotenv
from conftest import run_cli

load_dotenv()

def test_invalid_url(monkeypatch):
    # Отключаем TEST_URL и SINGBOX_URL на время теста
    monkeypatch.delenv("TEST_URL", raising=False)
    monkeypatch.delenv("SINGBOX_URL", raising=False)
    result = run_cli(["--dry-run", "-u", "https://invalid.url/doesnotexist.json", "-d", "2"])
    output = (result.stdout or "") + (result.stderr or "")
    assert (
        "error" in output.lower() or "ошибка" in output.lower() or result.returncode != 0
    ), f"stdout: {result.stdout}\nstderr: {result.stderr}\nreturncode: {result.returncode}"

def test_invalid_index():
    result = run_cli(["--index", "99", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    assert "no configuration found" in result.stdout.lower() or "ошибка" in result.stdout.lower() or result.returncode != 0 