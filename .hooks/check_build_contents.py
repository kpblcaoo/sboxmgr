#!/usr/bin/env python3
"""Pre-commit hook to verify wheel package integrity through import testing.

Creates a temporary virtual environment, installs the wheel, and tests
that all critical modules can be imported successfully.
"""

import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

# Critical modules that must be importable after wheel installation
REQUIRED_IMPORTS = [
    "sboxmgr.cli.main",
    "sboxmgr.configs.models",
    "sboxmgr.configs.manager",
    "sboxmgr.export.export_manager",
    "sboxmgr.subscription.manager.core",
    "sboxmgr.core.orchestrator",
    "logsetup.setup",
]

# Modules that may require special handling (logging, etc.)
OPTIONAL_IMPORTS = [
    "sboxmgr.configs.cli",  # May initialize logging
]


def create_temp_venv():
    """Create a temporary virtual environment."""
    temp_dir = tempfile.mkdtemp(prefix="wheel_test_")
    venv_path = Path(temp_dir) / "venv"

    print(f"🔧 Creating temporary venv: {venv_path}")
    venv.create(venv_path, with_pip=True)

    return venv_path, temp_dir


def install_wheel_in_venv(venv_path, wheel_file):
    """Install wheel in the temporary virtual environment."""
    pip_path = venv_path / "bin" / "pip"
    python_path = venv_path / "bin" / "python"

    print(f"📦 Installing wheel: {wheel_file.name}")

    try:
        # Install wheel
        subprocess.run(
            [str(pip_path), "install", str(wheel_file)],
            check=True,
            capture_output=True,
            text=True,
        )
        return python_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Wheel installation failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise


def test_imports(python_path, required_imports, optional_imports=None):
    """Test that all required modules can be imported."""
    print("🧪 Testing required imports...")

    failed_imports = []

    for module_name in required_imports:
        try:
            # Use subprocess to test import in the venv
            result = subprocess.run(
                [str(python_path), "-c", f"import {module_name}"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"✅ Import successful: {module_name}")
            else:
                print(f"❌ Import failed: {module_name}")
                print(f"Error: {result.stderr}")
                failed_imports.append(module_name)

        except Exception as e:
            print(f"❌ Import error for {module_name}: {e}")
            failed_imports.append(module_name)

    # Test optional imports (modules that may have side effects)
    if optional_imports:
        print("🧪 Testing optional imports...")
        for module_name in optional_imports:
            try:
                result = subprocess.run(
                    [str(python_path), "-c", f"import {module_name}"],
                    check=False,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print(f"✅ Optional import successful: {module_name}")
                else:
                    print(f"⚠️  Optional import failed: {module_name}")
                    print(f"Error: {result.stderr}")

            except Exception as e:
                print(f"⚠️  Optional import warning: {module_name}: {e}")
                # Don't fail on optional imports

    return failed_imports


def main():
    """Main function to check wheel integrity through import testing."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"

    # Clean previous builds
    print("🧹 Cleaning previous builds...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build wheel package
    print("🔨 Building wheel package...")
    try:
        subprocess.run(
            ["python", "-m", "build", "--wheel"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

    # Find wheel file
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("❌ No wheel file found in dist/")
        sys.exit(1)
    if len(wheel_files) > 1:
        print(f"❌ Multiple wheel files found in {dist_dir}:")
        for wheel in wheel_files:
            print(f"  - {wheel.name}")
        print("Please clean dist/ directory to ensure testing the correct wheel.")
        sys.exit(1)

    wheel_file = wheel_files[0]
    print(f"📦 Testing wheel: {wheel_file.name}")

    # Create temporary environment and test
    venv_path = None
    temp_dir = None

    try:
        venv_path, temp_dir = create_temp_venv()
        python_path = install_wheel_in_venv(venv_path, wheel_file)
        failed_imports = test_imports(python_path, REQUIRED_IMPORTS, OPTIONAL_IMPORTS)

        if failed_imports:
            print(f"❌ Wheel integrity check failed - failed imports: {failed_imports}")
            sys.exit(1)

        print("✅ Wheel integrity check passed - all critical modules importable")

    except Exception as e:
        print(f"❌ Wheel integrity check failed: {e}")
        sys.exit(1)

    finally:
        # Cleanup
        if temp_dir and Path(temp_dir).exists():
            print(f"🧹 Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
