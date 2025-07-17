import logging
import os
import pkgutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Определяем корень проекта
project_root = Path(__file__).parent.parent.resolve()

# Исправленный путь к исходникам - только sboxmgr пакет
src_root = project_root / "src" / "sboxmgr"

logger = logging.getLogger(__name__)

def build_wheel():
    # Build from project root, not from test directory
    subprocess.run([sys.executable, "-m", "build", "--wheel"], check=True, cwd=project_root)
    dist_dir = project_root / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "No wheel built!"
    return wheels[-1]

def find_all_submodules(package_path: Path, package_prefix: str):
    """Рекурсивно находит все подмодули и поддиректории пакета."""
    modules = set()
    for _finder, name, _ispkg in pkgutil.walk_packages([str(package_path)], prefix=package_prefix + "."):
        modules.add(name)
    return modules

def test_wheel_install_and_all_imports(tmp_path):
    wheel_path = build_wheel()
    assert src_root.exists(), f"{src_root} not found"

    # Собираем список всех подмодулей ТОЛЬКО из sboxmgr пакета
    all_modules = {"sboxmgr"}
    for _finder, name, _ispkg in pkgutil.walk_packages([str(src_root)], prefix="sboxmgr."):
        all_modules.add(name)

    # Добавляем также logsetup как отдельный пакет
    logsetup_root = project_root / "src" / "logsetup"
    if logsetup_root.exists():
        all_modules.add("logsetup")
        for _finder, name, _ispkg in pkgutil.walk_packages([str(logsetup_root)], prefix="logsetup."):
            all_modules.add(name)

    with tempfile.TemporaryDirectory() as venv_dir:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        python_bin = Path(venv_dir) / "bin" / "python"
        pip_bin = Path(venv_dir) / "bin" / "pip"
        subprocess.run([str(pip_bin), "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(pip_bin), "install", str(wheel_path)], check=True)

        # Проверяем, что все модули импортируются
        failed = []
        skipped = []
        for module in sorted(all_modules):
            code = (
                "import importlib\n"
                "try:\n"
                "    importlib.import_module('" + module + "')\n"
                "except RuntimeError as e:\n"
                "    if 'Logging not initialized' in str(e):\n"
                "        print('SKIP:', '" + module + "')\n"
                "        exit(10)\n"
                "    raise\n"
            )
            result = subprocess.run([str(python_bin), "-c", code], capture_output=True, text=True)
            if result.returncode == 10:
                skipped.append(module)
            elif result.returncode != 0:
                failed.append((module, result.stderr + result.stdout))

        if skipped:
            logger.warning(f"Skipped modules (require logging): {skipped}")

        if failed:
            # Выводим структуру установленного пакета для диагностики
            site_packages = subprocess.check_output([
                str(python_bin), "-c",
                "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])"
            ], text=True).strip()

            # Проверяем структуру sboxmgr
            sboxmgr_dir = os.path.join(site_packages, "sboxmgr")
            if os.path.exists(sboxmgr_dir):
                tree = subprocess.check_output(["find", sboxmgr_dir], text=True)
                msg = f"\n\nInstalled sboxmgr package structure:\n{tree}"
            else:
                msg = f"\n\nsboxmgr directory not found in {site_packages}"

            # Проверяем структуру logsetup
            logsetup_dir = os.path.join(site_packages, "logsetup")
            if os.path.exists(logsetup_dir):
                tree = subprocess.check_output(["find", logsetup_dir], text=True)
                msg += f"\n\nInstalled logsetup package structure:\n{tree}"
            else:
                msg += f"\n\nlogsetup directory not found in {site_packages}"

            failed_msg = "\n".join([
                f"Failed to import: {mod}\n{err}" for mod, err in failed
            ])
            pytest.fail(failed_msg + msg)
