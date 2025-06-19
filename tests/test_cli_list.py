import os
from dotenv import load_dotenv
load_dotenv()
from conftest import run_cli
import json

def test_list_servers_excluded():
    run_cli(["--exclude", "1", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "--dry-run"])
    result = run_cli(["--list-servers", "-u", os.getenv("TEST_URL", "https://example.com/sub-link"), "-d", "2"])
    assert "[excluded]" in result.stdout 