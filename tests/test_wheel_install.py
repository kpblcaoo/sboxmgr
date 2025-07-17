import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

CRITICAL_MODULES = [
    "sboxmgr.cli.main",
    "sboxmgr.config.loader",
    "sboxmgr.subscription.parsers.clash_parser",
    "sboxmgr.cli.commands.export",
    "sboxmgr.cli.commands.lang",
    "sboxmgr.cli.commands.exclusions",
    "sboxmgr.cli.commands.subscription",
    "sboxmgr.cli.commands.config",
    "sboxmgr.cli.commands.policy",
    "sboxmgr.configs.models",
    "sboxmgr.export.export_manager",
]

def build_wheel():
    subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True)
    dist_dir = Path("dist")
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No wheel built!"
    return wheels[-1]

def test_wheel_install_and_imports(tmp_path):
    wheel_path = build_wheel()
    with tempfile.TemporaryDirectory() as venv_dir:
        # 1. Create venv
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        python_bin = Path(venv_dir) / "bin" / "python"
        pip_bin = Path(venv_dir) / "bin" / "pip"
        # 2. Upgrade pip and install wheel
        subprocess.run([str(pip_bin), "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_bin), "install", str(wheel_path)], check=True)
        # 3. Check critical imports
        for module in CRITICAL_MODULES:
            code = f"import {module}"
            result = subprocess.run([str(python_bin), "-c", code], capture_output=True, text=True)
            assert result.returncode == 0, f"Failed to import {module} in wheel venv: {result.stderr}"
