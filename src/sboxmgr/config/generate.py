import os
import json
import subprocess
from logging import info, error
import tempfile
from sboxmgr.utils.env import get_config_file, get_backup_file, get_template_file
from sboxmgr.utils.file import atomic_write_json, file_exists, read_json, write_json

def generate_config(outbounds, template_file, config_file, backup_file, excluded_ips):
    """Generate sing-box configuration from template."""
    if not os.path.exists(template_file):
        error(f"Template file not found: {template_file}")
        raise FileNotFoundError(f"Template file not found: {template_file}")

    with open(template_file) as f:
        template = json.load(f)  # Load as JSON to manipulate

    # Prepare outbound tags for urltest
    outbound_tags = [outbound["tag"] for outbound in outbounds] if outbounds else []

    # Update the urltest's outbounds
    for outbound in template["outbounds"]:
        if outbound.get("type") == "urltest" and outbound.get("tag") == "auto":
            outbound["outbounds"] = outbound_tags
            break

    # Insert provider outbounds after urltest but before direct
    urltest_idx = next(
        (i for i, o in enumerate(template["outbounds"]) if o.get("tag") == "auto"),
        0
    )
    template["outbounds"] = (
        template["outbounds"][:urltest_idx + 1] +
        outbounds +
        template["outbounds"][urltest_idx + 1:]
    )

    # Ensure excluded_ips are in CIDR format
    excluded_ips_cidr = [f"{ip}/32" for ip in excluded_ips]

    # Debug log for excluded_ips
    info(f"Excluded IPs: {excluded_ips_cidr}")

    # Replace $excluded_servers with actual IPs in CIDR format
    for rule in template["route"]["rules"]:
        if rule.get("ip_cidr") == "$excluded_servers":
            rule["ip_cidr"] = excluded_ips_cidr

    # Write the temporary configuration using tempfile
    config = json.dumps(template, indent=2)
    
    # Ensure config_file directory exists
    config_dir = os.path.dirname(config_file)
    if not os.path.isdir(config_dir):
        error(f"Config directory does not exist: {config_dir}. "
              f"Set SBOXMGR_CONFIG_FILE to a writable path if your sing-box is installed elsewhere.")
        raise FileNotFoundError(f"Config directory does not exist: {config_dir}")

    if os.path.exists(config_file):
        with open(config_file, "r") as current_config_file:
            current_config = current_config_file.read()
            if current_config.strip() == config.strip():
                info("Configuration has not changed. Skipping update.")
                return False

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tmp:
        temp_config_file = tmp.name
        tmp.write(config)
    info(f"Temporary configuration written to {temp_config_file}")

    try:
        subprocess.run(["sing-box", "check", "-c", temp_config_file], check=True)
        info("Temporary configuration validated successfully")
    except FileNotFoundError:
        error("sing-box executable not found. Please install sing-box and ensure it is in your PATH.")
        os.unlink(temp_config_file)
        return False
    except subprocess.CalledProcessError as e:
        error(f"Temporary configuration is invalid or sing-box not found: {e}")
        os.unlink(temp_config_file)
        raise

    if os.path.exists(config_file):
        os.rename(config_file, backup_file)
        info(f"Created backup: {backup_file}")

    os.rename(temp_config_file, config_file)
    info(f"Configuration updated with {len(outbounds)} outbounds")
    return True

def generate_temp_config(outbounds, template_file, excluded_ips):
    """Генерирует json-строку конфига для dry-run без записи в файл."""
    if not os.path.exists(template_file):
        error(f"Template file not found: {template_file}")
        raise FileNotFoundError(f"Template file not found: {template_file}")
    with open(template_file) as f:
        template = json.load(f)
    outbound_tags = [outbound["tag"] for outbound in outbounds] if outbounds else []
    for outbound in template["outbounds"]:
        if outbound.get("type") == "urltest" and outbound.get("tag") == "auto":
            outbound["outbounds"] = outbound_tags
            break
    urltest_idx = next(
        (i for i, o in enumerate(template["outbounds"]) if o.get("tag") == "auto"),
        0
    )
    template["outbounds"] = (
        template["outbounds"][:urltest_idx + 1] +
        outbounds +
        template["outbounds"][urltest_idx + 1:]
    )
    excluded_ips_cidr = [f"{ip}/32" for ip in excluded_ips]
    for rule in template["route"]["rules"]:
        if rule.get("ip_cidr") == "$excluded_servers":
            rule["ip_cidr"] = excluded_ips_cidr
    return json.dumps(template, indent=2)

def validate_config_file(config_path):
    """Валидирует конфиг-файл через sing-box check. Возвращает (bool, вывод)."""
    import subprocess
    try:
        result = subprocess.run(["sing-box", "check", "-c", config_path], capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except FileNotFoundError:
        return False, "sing-box executable not found. Please install sing-box and ensure it is in your PATH."