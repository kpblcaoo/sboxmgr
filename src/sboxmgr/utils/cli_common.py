"""Common functions for CLI handlers to avoid circular imports."""

def load_outbounds(json_data, supported_protocols):
    """Load outbounds that are supported by the specified protocols.

    Args:
        json_data: JSON data containing outbounds, either dict with 'outbounds' key
                  or list of outbound objects.
        supported_protocols: List of protocol types to filter by.

    Returns:
        List of outbound objects that match the supported protocols.

    """
    if isinstance(json_data, dict) and "outbounds" in json_data:
        return [o for o in json_data["outbounds"] if o.get("type") in supported_protocols]
    return [o for o in json_data if o.get("type") in supported_protocols]
