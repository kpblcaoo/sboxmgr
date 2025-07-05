"""ID generation utilities for SBoxMgr."""

import hashlib
import json
from typing import Any, Dict

def generate_server_id(server):
    """Generate a unique identifier for a server configuration.
    
    Creates a SHA256 hash based on the server's tag, protocol type, and port
    to provide a stable, unique identifier for exclusion management and
    server tracking across subscription updates.
    
    Args:
        server: Server configuration dictionary containing 'tag', 'type', 
               and 'server_port' keys.
               
    Returns:
        Hexadecimal SHA256 hash string uniquely identifying the server.
        
    Note:
        The identifier is stable across subscription updates as long as
        the server's core attributes (tag, type, port) remain unchanged.

    """
    identifier = f"{server.get('tag', '')}{server.get('type', '')}{server.get('server_port', '')}"
    return hashlib.sha256(identifier.encode()).hexdigest() 