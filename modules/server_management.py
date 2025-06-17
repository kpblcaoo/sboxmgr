import json
import os
import hashlib
import fnmatch
import tempfile
import shutil
import datetime

EXCLUSION_FILE = os.getenv("SINGBOX_EXCLUSION_FILE", "./exclusions.json")

def list_servers(json_data, supported_protocols, debug_level=0):
    """List all supported outbounds with indices and details."""
    if isinstance(json_data, dict) and "outbounds" in json_data:
        servers = json_data["outbounds"]
    else:
        servers = json_data

    if debug_level >= 0:
        print("Index | Name | Protocol | Port")
        print("--------------------------------")
    index = 0
    for server in servers:
        # Only list supported outbounds
        if server.get("type") not in supported_protocols:
            continue
        # Extract the name from the 'tag' field if available
        name = server.get("tag", "N/A")
        protocol = server.get("type", "N/A")
        # Extract the port from the server configuration
        port = server.get("server_port", "N/A")
        if debug_level >= 0:
            print(f"{index} | {name} | {protocol} | {port}")
        index += 1

def generate_server_id(server):
    """Generate a unique ID for a server based on tag, protocol, and port."""
    identifier = f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
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

def exclude_servers(json_data, exclude_list, supported_protocols, debug_level=0):
    """Exclude servers by index or name, supporting wildcards."""
    exclusions = load_exclusions()
    servers = json_data.get("outbounds", json_data)
    new_exclusions = []

    # Create a list of supported servers with their indices
    supported_servers = [
        (idx, server) for idx, server in enumerate(servers)
        if server.get("type") in supported_protocols
    ]

    for item in exclude_list:
        if item.isdigit():
            # Exclude by index
            index = int(item)
            if 0 <= index < len(supported_servers):
                _, server = supported_servers[index]
                server_id = generate_server_id(server)
                new_exclusions.append({"id": server_id, "name": server.get("tag", "N/A")})
                if debug_level >= 0:
                    print(f"Excluding server by index {index}: {server.get('tag', 'N/A')}")
        else:
            # Exclude by name with wildcard support
            for _, server in supported_servers:
                if fnmatch.fnmatch(server.get("tag", ""), item):
                    server_id = generate_server_id(server)
                    new_exclusions.append({"id": server_id, "name": server.get("tag", "N/A")})
                    if debug_level >= 0:
                        print(f"Excluding server by name {server.get('tag', 'N/A')}")

    # Update exclusions
    exclusions["exclusions"].extend(new_exclusions)
    save_exclusions(exclusions)

def view_exclusions(debug_level=0):
    """View current exclusions."""
    exclusions = load_exclusions()
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