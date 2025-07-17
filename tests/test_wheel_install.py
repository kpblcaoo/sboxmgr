import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pkgutil
import importlib

import pytest

def build_wheel():
    subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True)
    dist_dir = Path("dist")
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No wheel built!"
    return wheels[-1]

def find_all_submodules(package_path: Path, package_prefix: str):
    """Рекурсивно находит все подмодули и поддиректории пакета."""
    modules = set()
    for finder, name, ispkg in pkgutil.walk_packages([str(package_path)], prefix=package_prefix + "."):
        modules.add(name)
    return modules

def test_wheel_install_and_all_imports(tmp_path):
    wheel_path = build_wheel()
    src_root = Path("src/sboxmgr")
    assert src_root.exists(), "src/sboxmgr not found"
    # Собираем список всех подмодулей из исходников
    all_modules = {"sboxmgr"}
    for finder, name, ispkg in pkgutil.walk_packages([str(src_root.parent)], prefix="sboxmgr."):
        all_modules.add(name)
    with tempfile.TemporaryDirectory() as venv_dir:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        python_bin = Path(venv_dir) / "bin" / "python"
        pip_bin = Path(venv_dir) / "bin" / "pip"
        subprocess.run([str(pip_bin), "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_bin), "install", str(wheel_path)], check=True)
        # Проверяем, что все модули импортируются
        failed = []
        for module in sorted(all_modules):
            code = f"try:\n import {module}\nexcept Exception as e:\n print('FAIL:', repr(e))\n exit(1)"
            result = subprocess.run([str(python_bin), "-c", code], capture_output=True, text=True)
            if result.returncode != 0:
                failed.append((module, result.stderr + result.stdout))
        if failed:
            # Выводим структуру установленного пакета для диагностики
            site_packages = subprocess.check_output([
                str(python_bin), "-c",
                "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])"
            ], text=True).strip()
            sboxmgr_dir = os.path.join(site_packages, "sboxmgr")
            tree = subprocess.check_output(["find", sboxmgr_dir], text=True)
            msg = "\n".join([
                f"Failed to import: {mod}\n{err}" for mod, err in failed
            ])
            msg += f"\n\nInstalled sboxmgr package structure:\n{tree}"
            pytest.fail(msg)
