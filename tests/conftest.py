import subprocess
import os
import shutil
import pytest
from pathlib import Path
import sys

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
    result = subprocess.run(
        [sys.executable, "src/main.py"] + args,
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