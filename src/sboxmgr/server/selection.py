from sboxmgr.server.exclusions import load_exclusions
from sboxmgr.utils.id import generate_server_id
import logging
import typer

def list_servers(json_data, supported_protocols, debug_level=0, dry_run=False):
    """
    List all supported outbounds with indices and details.
    Excluded servers помечаются как (excluded), индексация сквозная.
    """
    exclusions = load_exclusions(dry_run=dry_run)
    excluded_ids = {ex["id"] for ex in exclusions.get("exclusions", [])}
    servers = json_data.get("outbounds", json_data)

    # Выводим заголовок всегда
    typer.echo("Index | Name | Protocol | Port")
    typer.echo("--------------------------------")
    if debug_level >= 0:
        logging.info("Index | Name | Protocol | Port")
        logging.info("--------------------------------")
    for index, server in enumerate(servers):
        if server.get("type") not in supported_protocols:
            continue
        name = server.get("tag", "N/A")
        protocol = server.get("type", "N/A")
        port = server.get("server_port", "N/A")
        server_id = generate_server_id(server)
        if server_id in excluded_ids:
            name = f"{name} [excluded]"
        if debug_level >= 0:
            logging.info(f"{index} | {name} | {protocol} | {port}")
        typer.echo(f"{index} | {name} | {protocol} | {port}") 