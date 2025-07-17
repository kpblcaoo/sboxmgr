#!/usr/bin/env python3
"""Pre-commit hook to verify wheel package contains all required modules.

This script ensures that critical modules are included in the built wheel package
to prevent ModuleNotFoundError issues in production deployments.
"""

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main():
    """Main function to check wheel integrity."""
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

    wheel_file = wheel_files[0]
    print(f"📦 Checking wheel: {wheel_file.name}")

    # Check wheel contents
    required_modules = [
        "sboxmgr/configs/__init__.py",
        "logsetup/__init__.py",
    ]

    missing_modules = []

    with zipfile.ZipFile(wheel_file) as z:
        contents = z.namelist()

        for module in required_modules:
            if module not in contents:
                missing_modules.append(module)
            else:
                print(f"✅ Found: {module}")

    if missing_modules:
        print(f"❌ Missing required modules: {missing_modules}")
        print("Available modules:")
        for item in sorted(contents):
            if item.startswith(("sboxmgr/", "logsetup/")):
                print(f"  {item}")
        sys.exit(1)

    print("✅ Wheel integrity check passed - all required modules present")


if __name__ == "__main__":
    main()
