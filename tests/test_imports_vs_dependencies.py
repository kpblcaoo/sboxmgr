"""Test that all external imports are covered by pyproject.toml dependencies.

This test parses all .py files in the project, extracts all top-level imports,
and checks that every external (non-stdlib, non-local) import is present in pyproject.toml dependencies (main or optional).
"""

import ast
import importlib.util
import sys
from pathlib import Path

import pytest
import toml

# List of known stdlib modules (Python 3.9+)
# For full coverage, use sys.stdlib_module_names if available
try:
    STDLIB_MODULES = set(sys.stdlib_module_names)
except AttributeError:
    # Fallback for older Python
    import os
    import sysconfig

    STDLIB_MODULES = set(sys.builtin_module_names)
    stdlib_path = sysconfig.get_paths()["stdlib"]
    for _root, _dirs, files in os.walk(stdlib_path):
        for file in files:
            if file.endswith(".py"):
                STDLIB_MODULES.add(file[:-3])

# Project root and package name
top_dir = Path(__file__).parent.parent.resolve()
package_name = "sboxmgr"


def get_pyproject_dependencies() -> set:
    pyproject = toml.load(top_dir / "pyproject.toml")
    deps = set()
    for dep in pyproject.get("project", {}).get("dependencies", []):
        name = (
            dep.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("~=")[0]
            .split("!=")[0]
            .strip()
        )
        # Map known cases
        if name == "python-dotenv":
            name = "dotenv"
        if name == "pydantic-settings":
            name = "pydantic_settings"
        if name == "PyYAML":
            name = "yaml"
        deps.add(name.replace("-", "_"))
    # Add all optional dependencies
    for group in pyproject.get("project", {}).get("optional-dependencies", {}).values():
        for dep in group:
            name = (
                dep.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("~=")[0]
                .split("!=")[0]
                .strip()
            )
            if name == "python-dotenv":
                name = "dotenv"
            if name == "pydantic-settings":
                name = "pydantic_settings"
            if name == "PyYAML":
                name = "yaml"
            deps.add(name.replace("-", "_"))
    return deps


def is_external_import(module: str) -> bool:
    if module in STDLIB_MODULES:
        return False
    if module.startswith(package_name):
        return False
    if module.startswith("_"):
        return False
    # Filter out internal modules and test artifacts
    internal_modules = {
        "src",
        "tests",
        "logsetup",
        "sbox_common",
        "systemd",
        "cli",
        "conftest",
        "export",
        "utils",
        "configs",
    }
    if module in internal_modules:
        return False
    return True


def find_all_imports(py_path: Path) -> set:
    """Parse a .py file and return all top-level imported module names."""
    imports = set()
    with open(py_path, encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(py_path))
        except Exception:
            return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def test_external_imports_covered_by_dependencies():
    """Test that all external imports are present in pyproject.toml dependencies."""
    deps = get_pyproject_dependencies()
    all_imports = set()
    for py_file in top_dir.glob("src/**/*.py"):
        all_imports |= find_all_imports(py_file)
    for py_file in top_dir.glob("tests/**/*.py"):
        all_imports |= find_all_imports(py_file)
    missing = set()
    for module in all_imports:
        if is_external_import(module) and module not in deps:
            # Check if module is actually importable (to avoid false positives for unused/test code)
            if importlib.util.find_spec(module) is not None:
                missing.add(module)
    if missing:
        pytest.fail(
            f"External imports not covered by pyproject.toml dependencies (main or optional): {sorted(missing)}"
        )
    # Успех — ничего не делать, не возвращать True/False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
