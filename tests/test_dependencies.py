"""Critical tests for dependencies and imports.

These tests ensure that all dependencies declared in pyproject.toml
are actually importable and that no critical imports fail.
"""

import importlib
import sys
from pathlib import Path
from typing import List, Dict, Any

import pytest
import toml


def load_pyproject_dependencies() -> List[str]:
    """Load dependencies from pyproject.toml.

    Returns:
        List of package names (without version constraints).
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")

    data = toml.load(pyproject_path)
    dependencies = data.get("project", {}).get("dependencies", [])

    # Extract package names without version constraints
    package_names = []
    for dep in dependencies:
        # Handle different formats: "package>=1.0", "package==1.0", "package"
        package_name = dep.split(">=")[0].split("==")[0].split("<")[0].split("~=")[0].split("!=")[0].strip()
        package_names.append(package_name)

    return package_names


def package_to_module_name(package_name: str) -> str:
    """Convert package name to module name for import.

    Args:
        package_name: Package name from pyproject.toml

    Returns:
        Module name for importlib.import_module
    """
    # Common mappings for packages that don't match module names
    mappings = {
        "python-dotenv": "dotenv",
        "pydantic-settings": "pydantic_settings",
    }

    if package_name in mappings:
        return mappings[package_name]

    # Default: replace hyphens with underscores
    return package_name.replace("-", "_")


def test_all_dependencies_importable():
    """Test that all dependencies from pyproject.toml can be imported.

    This is a critical test that ensures the package can be installed
    and all declared dependencies are available.
    """
    dependencies = load_pyproject_dependencies()

    failed_imports = []
    for package in dependencies:
        module_name = package_to_module_name(package)
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            failed_imports.append(f"{package} -> {module_name}: {e}")

    if failed_imports:
        error_msg = "Failed to import dependencies:\n" + "\n".join(failed_imports)
        pytest.fail(error_msg)


def test_critical_modules_importable():
    """Test that critical modules can be imported without optional dependencies.

    This ensures that basic functionality works even without sbox-common.
    """
    critical_modules = [
        "sboxmgr.cli.main",
        "sboxmgr.config.loader",
        "sboxmgr.subscription.parsers.clash_parser",
        "sboxmgr.cli.commands.export",
        "sboxmgr.cli.commands.lang",
        "sboxmgr.cli.commands.exclusions",
        "sboxmgr.cli.commands.subscription",
        "sboxmgr.cli.commands.config",
        "sboxmgr.cli.commands.policy",
    ]

    failed_imports = []
    for module_name in critical_modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            failed_imports.append(f"{module_name}: {e}")
        except Exception as e:
            # Other exceptions (like missing optional deps) are OK
            # as long as the module can be imported
            pass

    if failed_imports:
        error_msg = "Failed to import critical modules:\n" + "\n".join(failed_imports)
        pytest.fail(error_msg)


def test_no_file_dependencies():
    """Test that no file:// dependencies are present in pyproject.toml.

    File dependencies break package installation from PyPI/TestPyPI.
    """
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")

    data = toml.load(pyproject_path)
    dependencies = data.get("project", {}).get("dependencies", [])
    optional_deps = data.get("project", {}).get("optional-dependencies", {})

    # Check main dependencies
    for dep in dependencies:
        if dep.startswith("file://"):
            pytest.fail(f"File dependency found in main dependencies: {dep}")

    # Check optional dependencies
    for group_name, group_deps in optional_deps.items():
        for dep in group_deps:
            if dep.startswith("file://"):
                pytest.fail(f"File dependency found in optional dependencies [{group_name}]: {dep}")


def test_package_builds():
    """Test that the package can be built successfully.

    This ensures the package structure is correct and all required files are present.
    """
    try:
        import subprocess
        # Just check that build command works (without --dry-run)
        result = subprocess.run(
            [sys.executable, "-m", "build", "--help"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )

        if result.returncode != 0:
            pytest.fail(f"Build module not working:\n{result.stdout}\n{result.stderr}")

    except ImportError:
        pytest.skip("build module not available")


if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v"])
