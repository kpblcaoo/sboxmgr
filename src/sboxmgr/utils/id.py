import hashlib

def generate_server_id(server):
    """Generate a unique ID for a server based on tag, protocol, and port."""
    identifier = f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
    return hashlib.sha256(identifier.encode()).hexdigest() 