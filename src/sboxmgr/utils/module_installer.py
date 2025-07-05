"""Module installer utilities for SBoxMgr."""

import subprocess
import sys
import logging

# Function to install dependencies from requirements.txt

def install_dependencies():
    """Install dependencies from requirements.txt."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        logging.info("Dependencies installed successfully.")
    except Exception as e:
        logging.error(f"Error installing dependencies: {e}")

if __name__ == "__main__":
    install_dependencies() 