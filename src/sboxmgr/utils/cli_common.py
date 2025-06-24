"""
Общие функции для CLI-обработчиков, чтобы избежать циклических импортов.
"""

def load_outbounds(json_data, supported_protocols):
    """Возвращает список outbounds, поддерживаемых протоколами."""
    if isinstance(json_data, dict) and "outbounds" in json_data:
        return [o for o in json_data["outbounds"] if o.get("type") in supported_protocols]
    return [o for o in json_data if o.get("type") in supported_protocols] 