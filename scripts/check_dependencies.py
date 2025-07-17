#!/usr/bin/env python3
"""Script to check all dependencies and imports in sboxmgr.

This script verifies that all required dependencies are available
and that no critical imports fail.
"""

import importlib
import sys

# Core dependencies that should always be available
CORE_DEPS = [
    "typer",
    "requests",
    "dotenv",  # python-dotenv package
    "pydantic",
    "pydantic-settings",
    "packaging",
    "toml",
    "textual",
    "yaml",  # PyYAML
]

# Optional dependencies
OPTIONAL_DEPS = [
    "sbox_common",  # Only needed for IPC functionality
]

# Critical modules that should import without sbox-common
CRITICAL_MODULES = [
    "sboxmgr.cli.main",
    "sboxmgr.config.loader",
    "sboxmgr.subscription.parsers.clash_parser",
    "sboxmgr.cli.commands.export",
    "sboxmgr.cli.commands.lang",
    "sboxmgr.cli.commands.exclusions",
]

def check_dependency(module_name: str, required: bool = True) -> bool:
    """Check if a dependency can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        if required:
            print(f"❌ {module_name} - {e}")
            return False
        else:
            print(f"⚠️  {module_name} - {e} (optional)")
            return True

def check_module_import(module_name: str) -> bool:
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {module_name} - {e} (imported but error)")
        return True

def main():
    """Main function to check all dependencies."""
    print("🔍 Checking sboxmgr dependencies...\n")

    # Check core dependencies
    print("📦 Core Dependencies:")
    core_ok = all(check_dependency(dep, required=True) for dep in CORE_DEPS)

    print("\n📦 Optional Dependencies:")
    optional_ok = all(check_dependency(dep, required=False) for dep in OPTIONAL_DEPS)

    # Check critical modules
    print("\n🔧 Critical Modules:")
    modules_ok = all(check_module_import(module) for module in CRITICAL_MODULES)

    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    print(f"Core dependencies: {'✅ OK' if core_ok else '❌ FAILED'}")
    print(f"Optional dependencies: {'✅ OK' if optional_ok else '⚠️  WARNINGS'}")
    print(f"Critical modules: {'✅ OK' if modules_ok else '❌ FAILED'}")

    if core_ok and modules_ok:
        print("\n🎉 All critical dependencies and modules are working!")
        print("✅ sboxmgr should work without sbox-common")
        return 0
    else:
        print("\n❌ Some critical dependencies or modules failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
