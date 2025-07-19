#!/usr/bin/env python3
"""Quick import check for pre-commit hooks.

Performs fast import testing of critical modules without building wheel.
This is a lightweight alternative to the full wheel integrity check.
"""

import sys

# Critical modules that must be importable
CRITICAL_IMPORTS = [
    "sboxmgr.cli.main",
    "sboxmgr.configs.models",
    "sboxmgr.configs.manager",
    "sboxmgr.export.export_manager",
    "sboxmgr.subscription.manager.core",
    "sboxmgr.core.orchestrator",
    "logsetup.setup",
]

# Modules that may have side effects (logging, etc.)
OPTIONAL_IMPORTS = [
    "sboxmgr.configs.cli",
]


def test_import(module_name: str) -> bool:
    """Test if a module can be imported successfully.

    Args:
        module_name: Name of the module to test

    Returns:
        True if import successful, False otherwise

    """
    try:
        __import__(module_name)
        return True
    except ImportError as e:
        print(f"❌ Import failed: {module_name}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Import warning: {module_name}")
        print(f"   Error: {e}")
        # Don't fail on non-ImportError exceptions
        return True


def main():
    """Main function to perform quick import checks."""
    print("🔍 Quick import check...")

    failed_imports = []

    # Test critical imports
    for module_name in CRITICAL_IMPORTS:
        if not test_import(module_name):
            failed_imports.append(module_name)
        else:
            print(f"✅ {module_name}")

    # Test optional imports (warnings only)
    for module_name in OPTIONAL_IMPORTS:
        test_import(module_name)

    if failed_imports:
        print(f"\n❌ Quick import check failed - failed imports: {failed_imports}")
        print(
            "💡 Run 'python .hooks/check_build_contents.py' for full wheel integrity check"
        )
        sys.exit(1)

    print("✅ Quick import check passed")


if __name__ == "__main__":
    main()
