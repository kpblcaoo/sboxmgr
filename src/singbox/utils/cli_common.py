"""
Общие функции для CLI-обработчиков, чтобы избежать циклических импортов.
Здесь размещаются функции типа load_outbounds, prepare_selection и др.
"""

def load_outbounds(json_data, supported_protocols):
    """Возвращает список outbounds, поддерживаемых протоколами."""
    if isinstance(json_data, dict) and "outbounds" in json_data:
        return [o for o in json_data["outbounds"] if o.get("type") in supported_protocols]
    return [o for o in json_data if o.get("type") in supported_protocols]


def prepare_selection(json_data, indices, remarks, supported_protocols, exclusions, debug_level=0, dry_run=False):
    """
    Унифицированная логика выбора серверов по индексу/remarks с учётом exclusions.
    Возвращает (outbounds, excluded_ips, selected_servers).
    """
    from singbox.config.fetch import select_config
    from singbox.config.protocol import validate_protocol
    from singbox.utils.id import generate_server_id
    from singbox.server.management import apply_exclusions

    excluded_ids = {ex["id"] for ex in exclusions.get("exclusions", [])}
    outbounds = []
    excluded_ips = []
    selected_servers = []

    if remarks or indices:
        try:
            if isinstance(indices, list) and len(indices) > 1:
                for idx in indices:
                    config = select_config(json_data, remarks, idx, dry_run=dry_run)
                    outbound = validate_protocol(config, supported_protocols)
                    outbounds.append(outbound)
                    if "server" in outbound:
                        if outbound["server"] in excluded_ids:
                            import logging
                            logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                        excluded_ips.append(outbound["server"])
                    selected_servers.append({"index": idx, "id": generate_server_id(outbound)})
                    if debug_level >= 1:
                        import logging
                        logging.info(f"Selected server at index {idx}")
                    if debug_level >= 2:
                        import logging
                        logging.debug(f"Selected configuration details: {config}")
            else:
                idx = indices[0] if indices else None
                config = select_config(json_data, remarks, idx, dry_run=dry_run)
                outbound = validate_protocol(config, supported_protocols)
                outbounds = [outbound]
                if "server" in outbound:
                    if outbound["server"] in excluded_ids:
                        import logging
                        logging.warning(f"Server {outbound['server']} at index {idx} is in the exclusion list.")
                    excluded_ips.append(outbound["server"])
                selected_servers = [{"index": idx, "id": generate_server_id(outbound)}]
                if debug_level >= 1:
                    import logging
                    logging.info(f"Selected server at index {idx}")
                if debug_level >= 2:
                    import logging
                    logging.debug(f"Selected configuration details: {config}")
        except ValueError as e:
            print(f"[Ошибка] {e}")
            return [], [], []
    else:
        if not json_data:
            print("Error: URL is required for auto-selection.")
            return [], [], []
        if isinstance(json_data, dict) and "outbounds" in json_data:
            configs = [
                outbound for outbound in json_data["outbounds"]
                if outbound.get("type") in supported_protocols
            ]
        else:
            configs = json_data
        configs = apply_exclusions(configs, excluded_ids, debug_level)
        for idx, config in enumerate(configs):
            try:
                outbound = validate_protocol(config, supported_protocols)
                if not outbound["tag"].startswith("proxy-"):
                    outbounds.append(outbound)
                else:
                    outbound["tag"] = f"proxy-{chr(97 + idx)}"
                    outbounds.append(outbound)
                if "server" in outbound:
                    excluded_ips.append(outbound["server"])
            except ValueError as e:
                import logging
                logging.warning(f"Skipping invalid configuration at index {idx}: {e}")
        if not outbounds:
            import logging
            logging.warning("No valid configurations found for auto-selection, using direct")
            outbounds = []
        if debug_level >= 1:
            import logging
            logging.info(f"Prepared {len(outbounds)} servers for auto-selection")
            logging.info(f"Excluded IPs: {excluded_ips}")
    return outbounds, excluded_ips, selected_servers 