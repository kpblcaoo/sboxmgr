from conftest import run_cli
import os
import json

def test_excluded_index():
    run_cli(["--exclude", "1", "-u", "https://example.com/sub-link", "--dry-run"])
    result = run_cli(["--index", "1", "-u", "https://example.com/sub-link", "--dry-run"])
    assert "excluded" in result.stdout or "исключён" in result.stdout or "Ошибка" in result.stdout

def test_excluded_remarks():
    run_cli(["--exclude", "1", "-u", "https://example.com/sub-link", "--dry-run"])
    result = run_cli(["--remarks", "[NL-2]  vless-reality", "-u", "https://example.com/sub-link", "--dry-run"])
    assert "excluded" in result.stdout or "исключён" in result.stdout or "Ошибка" in result.stdout 