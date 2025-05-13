import os
import json
import subprocess
from logging import info, error

def generate_config(outbound, template_file, config_file, backup_file):
    """Generate sing-box configuration from template."""
    if not os.path.exists(template_file):
        error(f"Template file not found: {template_file}")
        raise FileNotFoundError(f"Template file not found: {template_file}")

    temp_config_file = f"{config_file}.tmp"

    with open(template_file) as f:
        template = f.read()

    config = template.replace("$outbound_json", json.dumps(outbound, indent=2))

    if os.path.exists(config_file):
        with open(config_file, "r") as current_config_file:
            current_config = current_config_file.read()
            if current_config.strip() == config.strip():
                info("Configuration has not changed. Skipping update.")
                return False

    with open(temp_config_file, "w") as f:
        f.write(config)
    info(f"Temporary configuration written to {temp_config_file}")

    try:
        subprocess.run(["sing-box", "check", "-c", temp_config_file], check=True)
        info("Temporary configuration validated successfully")
    except (subprocess.CalledProcessError, FileNotFoundError):
        error("Temporary configuration is invalid or sing-box not found")
        raise

    if os.path.exists(config_file):
        os.rename(config_file, backup_file)
        info(f"Created backup: {backup_file}")

    os.rename(temp_config_file, config_file)
    info(f"Configuration updated for {outbound['type']}")
    return True
