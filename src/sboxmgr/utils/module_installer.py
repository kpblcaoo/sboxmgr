"""Module installer utilities for SBoxMgr."""

import subprocess
import sys
import logging

# Function to install dependencies from requirements.txt

def install_dependencies():
    """Install Python dependencies from requirements.txt file.

    Executes pip install command to install all packages listed in
    requirements.txt using the current Python interpreter.

    Raises:
        subprocess.CalledProcessError: If pip install command fails.
        Exception: For other installation errors.

    Note:
        This function logs success/failure messages and does not return
        a value. Check logs for installation status.

    """
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logging.info("Dependencies installed successfully.")
    except Exception as e:
        logging.error(f"Error installing dependencies: {e}")

if __name__ == "__main__":
    install_dependencies()
