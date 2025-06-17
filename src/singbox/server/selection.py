from singbox.server.exclusions import load_exclusions
from singbox.utils.id import generate_server_id

def list_servers(json_data, supported_protocols, debug_level=0):
    """
    List all supported outbounds with indices and details.
    Excluded servers помечаются как (excluded), индексация сквозная.
    """
    exclusions = load_exclusions()
    excluded_ids = {ex["id"] for ex in exclusions["exclusions"]}
    if isinstance(json_data, dict) and "outbounds" in json_data:
        servers = json_data["outbounds"]
    else:
        servers = json_data

    if debug_level >= 0:
        print("Index | Name | Protocol | Port")
        print("--------------------------------")
    for index, server in enumerate(servers):
        if server.get("type") not in supported_protocols:
            continue
        name = server.get("tag", "N/A")
        protocol = server.get("type", "N/A")
        port = server.get("server_port", "N/A")
        server_id = generate_server_id(server)
        if server_id in excluded_ids:
            name += " [excluded]"
        if debug_level >= 0:
            print(f"{index} | {name} | {protocol} | {port}") 