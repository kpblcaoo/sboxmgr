"""Server exclusions management utilities.

This module provides functions for managing server exclusions - servers that
should be filtered out during subscription processing. Exclusions are stored
in JSON format and applied during the pipeline to remove unwanted servers
based on various criteria.
"""

import json
import datetime
import fnmatch
import logging
import typer
from sboxmgr.utils.id import generate_server_id
from sboxmgr.utils.env import get_exclusion_file
from sboxmgr.utils.file import atomic_write_json, atomic_remove, file_exists, read_json

def load_exclusions(dry_run=False):
    """Load exclusions from the exclusion file."""
    EXCLUSION_FILE = get_exclusion_file()
    if file_exists(EXCLUSION_FILE):
        try:
            return read_json(EXCLUSION_FILE)
        except json.JSONDecodeError:
            if not dry_run:
                logging.error(f"Файл {EXCLUSION_FILE} повреждён или невалиден. Игнорируем содержимое и продолжаем с пустым списком исключений.")
                typer.echo("[Ошибка] exclusions.json повреждён или невалиден. Сброшен до пустого состояния.")
            return {"last_modified": "", "exclusions": []}
    return {"last_modified": "", "exclusions": []}

def save_exclusions(exclusions):
    """Save exclusions to the exclusion file."""
    EXCLUSION_FILE = get_exclusion_file()
    exclusions["last_modified"] = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")
    atomic_write_json(exclusions, EXCLUSION_FILE)

def exclude_servers(json_data, exclude_list, supported_protocols, debug_level=0):
    """Exclude servers by index or name, supporting wildcards."""
    exclusions = load_exclusions(dry_run=False)
    servers = json_data.get("outbounds", json_data)
    new_exclusions = []
    supported_servers = [
        (idx, server) for idx, server in enumerate(servers)
        if server.get("type") in supported_protocols
    ]
    existing_ids = {ex["id"] for ex in exclusions["exclusions"]}
    for item in exclude_list:
        if item.isdigit():
            index = int(item)
            if 0 <= index < len(supported_servers):
                _, server = supported_servers[index]
                server_id = generate_server_id(server)
                name = f"{server.get('tag', 'N/A')} ({server.get('type', 'N/A')}:{server.get('server_port', 'N/A')})"
                if server_id not in existing_ids:
                    new_exclusions.append({"id": server_id, "name": name})
                    existing_ids.add(server_id)
                    if debug_level >= 0:
                        logging.info(f"Excluding server by index {index}: {name}")
                        typer.echo(f"Excluding server by index {index}: {name}")
                else:
                    if debug_level >= 0:
                        logging.info(f"[Info] Server already excluded: {name}")
                        typer.echo(f"already excluded: {name}")
        else:
            for _, server in supported_servers:
                if fnmatch.fnmatch(server.get("tag", ""), item):
                    server_id = generate_server_id(server)
                    name = f"{server.get('tag', 'N/A')} ({server.get('type', 'N/A')}:{server.get('server_port', 'N/A')})"
                    if server_id not in existing_ids:
                        new_exclusions.append({"id": server_id, "name": name})
                        existing_ids.add(server_id)
                        if debug_level >= 0:
                            logging.info(f"Excluding server by name {name}")
                            typer.echo(f"Excluding server by name {name}")
                    else:
                        if debug_level >= 0:
                            logging.info(f"[Info] Server already excluded: {name}")
                            typer.echo(f"already excluded: {name}")
    exclusions["exclusions"].extend(new_exclusions)
    save_exclusions(exclusions)

def remove_exclusions(exclude_list, json_data, supported_protocols, debug_level=0):
    """Remove exclusions by index or name."""
    exclusions = load_exclusions(dry_run=False)
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
                    logging.info(f"Removed exclusion for server at index {index}: {server.get('tag', 'N/A')}")
                    typer.echo(f"Removed exclusion for server at index {index}: {server.get('tag', 'N/A')}")
    exclusions["exclusions"] = new_exclusions
    save_exclusions(exclusions)

def view_exclusions(debug_level=0):
    """View current exclusions."""
    exclusions = load_exclusions(dry_run=False)
    typer.echo("Current Exclusions:")
    for exclusion in exclusions["exclusions"]:
        typer.echo(f"ID: {exclusion['id']}, Name: {exclusion['name']}, Reason: {exclusion.get('reason', 'N/A')}")
    if debug_level >= 2:
        logging.debug(json.dumps(exclusions, indent=2))

def clear_exclusions():
    """Clear all current exclusions."""
    EXCLUSION_FILE = get_exclusion_file()
    if file_exists(EXCLUSION_FILE):
        try:
            atomic_remove(EXCLUSION_FILE)
            logging.info("Exclusions cleared.")
            typer.echo("Exclusions cleared.")
        except Exception as e:
            logging.error(f"[Ошибка] Не удалось удалить exclusions.json: {e}")
            typer.echo(f"[Ошибка] Не удалось удалить exclusions.json: {e}", err=True)
    else:
        logging.info("No exclusions to clear.")
        typer.echo("No exclusions to clear.") 