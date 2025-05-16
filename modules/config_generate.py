import os
import json
import subprocess
from logging import info, error

def generate_config(outbounds, template_file, config_file, backup_file, excluded_ips):
    """Generate sing-box configuration from template."""
    if not os.path.exists(template_file):
        error(f"Template file not found: {template_file}")
        raise FileNotFoundError(f"Template file not found: {template_file}")

    temp_config_file = f"{config_file}.tmp"

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

    # Write the temporary configuration
    config = json.dumps(template, indent=2)
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
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        error(f"Temporary configuration is invalid or sing-box not found: {e}")
        raise

    if os.path.exists(config_file):
        os.rename(config_file, backup_file)
        info(f"Created backup: {backup_file}")

    os.rename(temp_config_file, config_file)
    info(f"Configuration updated with {len(outbounds)} outbounds")
    return True