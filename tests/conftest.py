import subprocess
import os
import shutil
import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Patch logging before any imports that might trigger it
patch('logsetup.setup.setup_logging').start()
patch('logsetup.setup.rotate_logs').start()

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

def run_cli(args, env=None, cwd=None):
    """Вспомогательная функция для вызова CLI с capture_output.
    exclusions.json и selected_config.json будут создаваться в cwd (tmp_path) через env.
    """
    if env is None:
        env = os.environ.copy()
    # Указать файлы в tmp_path
    cwd = cwd or os.getcwd()
    env["SBOXMGR_EXCLUSION_FILE"] = str(Path(cwd) / "exclusions.json")
    env["SBOXMGR_SELECTED_CONFIG_FILE"] = str(Path(cwd) / "selected_config.json")
    # Использовать временный лог файл для тестов
    env["SBOXMGR_LOG_FILE"] = str(Path(cwd) / "test.log")
    result = subprocess.run(
        [sys.executable, "src/sboxmgr/cli/main.py"] + args,
        capture_output=True, text=True, env=env, cwd=PROJECT_ROOT
    )
    return result

@pytest.fixture(autouse=True)
def cleanup_files(tmp_path, monkeypatch):
    """Фикстура: каждый тест работает в своём tmp_path, файлы очищаются автоматически."""
    monkeypatch.chdir(tmp_path)
    for fname in ["exclusions.json", "selected_config.json"]:
        if os.path.exists(fname):
            os.remove(fname)
    yield
    # После теста — ещё раз чистим
    for fname in ["exclusions.json", "selected_config.json"]:
        if os.path.exists(fname):
            os.remove(fname)

@pytest.fixture(autouse=True)
def mock_logging_setup():
    """Mock logging setup to prevent permission errors during test collection."""
    with patch('logsetup.setup.setup_logging') as mock_setup, \
         patch('logsetup.setup.rotate_logs') as mock_rotate:
        mock_setup.return_value = None
        mock_rotate.return_value = None
        yield 