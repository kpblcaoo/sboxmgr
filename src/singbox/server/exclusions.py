import json
import os
import datetime
import fnmatch

def load_exclusions():
    """Load exclusions from the exclusion file."""
    EXCLUSION_FILE = os.getenv("SINGBOX_EXCLUSION_FILE", "./exclusions.json")
    if os.path.exists(EXCLUSION_FILE):
        with open(EXCLUSION_FILE, 'r') as f:
            return json.load(f)
    return {"last_modified": "", "exclusions": []}

def save_exclusions(exclusions):
    """Save exclusions to the exclusion file."""
    EXCLUSION_FILE = os.getenv("SINGBOX_EXCLUSION_FILE", "./exclusions.json")
    exclusions["last_modified"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(EXCLUSION_FILE, 'w') as f:
        json.dump(exclusions, f, indent=2)

def exclude_servers(json_data, exclude_list, supported_protocols, debug_level=0):
    """Exclude servers by index or name, supporting wildcards."""
    exclusions = load_exclusions()
    servers = json_data.get("outbounds", json_data)
    new_exclusions = []
    supported_servers = [
        (idx, server) for idx, server in enumerate(servers)
        if server.get("type") in supported_protocols
    ]
    for item in exclude_list:
        if item.isdigit():
            index = int(item)
            if 0 <= index < len(supported_servers):
                _, server = supported_servers[index]
                server_id = server.get('id', None) or f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
                new_exclusions.append({"id": server_id, "name": server.get("tag", "N/A")})
                if debug_level >= 0:
                    print(f"Excluding server by index {index}: {server.get('tag', 'N/A')}")
        else:
            for _, server in supported_servers:
                if fnmatch.fnmatch(server.get("tag", ""), item):
                    server_id = server.get('id', None) or f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
                    new_exclusions.append({"id": server_id, "name": server.get("tag", "N/A")})
                    if debug_level >= 0:
                        print(f"Excluding server by name {server.get('tag', 'N/A')}")
    exclusions["exclusions"].extend(new_exclusions)
    save_exclusions(exclusions)

def remove_exclusions(exclude_list, json_data, supported_protocols, debug_level=0):
    """Remove exclusions by index or name."""
    exclusions = load_exclusions()
    servers = json_data.get("outbounds", json_data)
    supported_servers = [
        (idx, server) for idx, server in enumerate(servers)
        if server.get("type") in supported_protocols
    ]
    new_exclusions = exclusions["exclusions"]
    for item in exclude_list:
        if item.startswith('-') and item[1:].isdigit():
            index = int(item[1:])
            if 0 <= index < len(supported_servers):
                _, server = supported_servers[index]
                server_id = server.get('id', None) or f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
                new_exclusions = [ex for ex in new_exclusions if ex["id"] != server_id]
                if debug_level >= 0:
                    print(f"Removed exclusion for server at index {index}: {server.get('tag', 'N/A')}")
    exclusions["exclusions"] = new_exclusions
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
    EXCLUSION_FILE = os.getenv("SINGBOX_EXCLUSION_FILE", "./exclusions.json")
    if os.path.exists(EXCLUSION_FILE):
        os.remove(EXCLUSION_FILE)
        print("Exclusions cleared.")
    else:
        print("No exclusions to clear.") 