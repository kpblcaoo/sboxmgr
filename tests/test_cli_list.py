from conftest import run_cli
import os
import json

def test_list_servers_excluded():
    run_cli(["--exclude", "1", "-u", "https://example.com/sub-link", "--dry-run"])
    result = run_cli(["--list-servers", "-u", "https://example.com/sub-link", "-d", "2"])
    assert "[excluded]" in result.stdout 