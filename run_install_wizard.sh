#!/bin/bash

# Path to the virtual environment
VENV_PATH="/opt/update_singbox/venv"

# Activate the virtual environment
source "$VENV_PATH/bin/activate"

# Run the installation wizard
python3 install_wizard.py "$@" 