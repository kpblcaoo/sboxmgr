import json
import os
import hashlib
import fnmatch
import tempfile
import shutil
import datetime

EXCLUSION_FILE = os.getenv("SINGBOX_EXCLUSION_FILE", "./exclusions.json")

def list_servers(json_data):
    """List all servers with indices and details."""
    if isinstance(json_data, dict) and "outbounds" in json_data:
        servers = json_data["outbounds"]
    else:
        servers = json_data

    print("Index | Name | Protocol | Port")
    print("--------------------------------")
    for idx, server in enumerate(servers):
        # Extract the name from the 'tag' field if available
        name = server.get("tag", "N/A")
        protocol = server.get("type", "N/A")
        port = server.get("port", "N/A")
        print(f"{idx} | {name} | {protocol} | {port}")

def generate_server_id(server):
    """Generate a unique ID for a server based on name, protocol, and port."""
    identifier = f"{server.get('name', '')}{server.get('type', '')}{server.get('port', '')}"
    return hashlib.sha256(identifier.encode()).hexdigest()

def handle_temp_file(content, target_path, validate_fn):
    """Handle temporary file creation and validation."""
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(target_path))
    with open(temp_path, 'w') as f:
        f.write(json.dumps(content, indent=2))
    if validate_fn(temp_path):
        shutil.move(temp_path, target_path)
    else:
        raise ValueError(f"Validation failed for {temp_path}")

def load_exclusions():
    """Load exclusions from the exclusion file."""
    if os.path.exists(EXCLUSION_FILE):
        with open(EXCLUSION_FILE, 'r') as f:
            return json.load(f)
    return {"last_modified": "", "exclusions": []}

def save_exclusions(exclusions):
    """Save exclusions to the exclusion file."""
    exclusions["last_modified"] = datetime.datetime.utcnow().isoformat() + "Z"
    handle_temp_file(exclusions, EXCLUSION_FILE, lambda x: True)  # Add proper validation

def apply_exclusions(configs, excluded_ids, debug_level):
    """Apply exclusions to the list of server configurations."""
    valid_configs = []
    for idx, config in enumerate(configs):
        server_id = generate_server_id(config)
        if server_id in excluded_ids:
            if debug_level >= 1:
                print(f"Skipping server {config.get('name', 'N/A')} (ID: {server_id}) due to exclusion.")
            continue
        valid_configs.append(config)
    return valid_configs

def exclude_servers(json_data, exclude_list, debug_level):
    """Exclude servers by index or name, supporting wildcards."""
    exclusions = load_exclusions()
    servers = json_data.get("outbounds", json_data)
    new_exclusions = []

    for item in exclude_list:
        if item.isdigit():
            # Exclude by index
            index = int(item)
            if 0 <= index < len(servers):
                server = servers[index]
                server_id = generate_server_id(server)
                new_exclusions.append({"id": server_id, "name": server.get("name", "N/A")})
                if debug_level >= 1:
                    print(f"Excluding server by index {index}: {server.get('name', 'N/A')}")
        else:
            # Exclude by name with wildcard support
            for server in servers:
                if fnmatch.fnmatch(server.get("name", ""), item):
                    server_id = generate_server_id(server)
                    new_exclusions.append({"id": server_id, "name": server.get("name", "N/A")})
                    if debug_level >= 1:
                        print(f"Excluding server by name {server.get('name', 'N/A')}")

    # Update exclusions
    exclusions["exclusions"].extend(new_exclusions)
    save_exclusions(exclusions)

def view_exclusions(debug_level):
    """View current exclusions."""
    exclusions = load_exclusions()
    if debug_level >= 1:
        print("Current Exclusions:")
        for exclusion in exclusions["exclusions"]:
            print(f"ID: {exclusion['id']}, Name: {exclusion['name']}, Reason: {exclusion.get('reason', 'N/A')}")
    if debug_level >= 2:
        print(json.dumps(exclusions, indent=2))

def clear_exclusions():
    """Clear all current exclusions."""
    if os.path.exists(EXCLUSION_FILE):
        os.remove(EXCLUSION_FILE)
        print("Exclusions cleared.")
    else:
        print("No exclusions to clear.") 