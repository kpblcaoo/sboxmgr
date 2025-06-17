from conftest import run_cli

def test_invalid_url():
    result = run_cli(["--dry-run", "-u", "https://invalid.url/doesnotexist.json", "-d", "2"])
    assert "error" in result.stdout.lower() or "ошибка" in result.stdout.lower() or result.returncode != 0

def test_invalid_index():
    result = run_cli(["--index", "99", "-u", "https://example.com/sub-link", "--dry-run"])
    assert "no configuration found" in result.stdout.lower() or "ошибка" in result.stdout.lower() or result.returncode != 0 