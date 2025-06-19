import typer
import os
import sys
import logging
from dotenv import load_dotenv
from sboxmgr.config.fetch import fetch_json
from sboxmgr.utils.cli_common import prepare_selection
from sboxmgr.config.generate import generate_config
from sboxmgr.service.manage import manage_service
from sboxmgr.server.exclusions import load_exclusions, exclude_servers, remove_exclusions, view_exclusions
from sboxmgr.server.state import load_selected_config, save_selected_config
from sboxmgr.server.selection import list_servers as do_list_servers

load_dotenv()

app = typer.Typer(help="sboxctl: Sing-box config manager (exclusions, dry-run, selection, etc.)")

SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

@app.command()
def run(
    url: str = typer.Option(
        ..., "-u", "--url", help="Config subscription URL",
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    remarks: str = typer.Option(None, "-r", "--remarks", help="Select server by remarks"),
    index: str = typer.Option(None, "-i", "--index", help="Select server by index (comma-separated)"),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug level: 0=min, 1=info, 2=debug"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate config only, do not write"),
    config_file: str = typer.Option(None, "--config-file", help="Path to config.json (overrides env)"),
    backup_file: str = typer.Option(None, "--backup-file", help="Path to config.json.bak (overrides env)"),
    template_file: str = typer.Option(None, "--template-file", help="Path to config.template.json (overrides env)"),
):
    """Generate and apply sing-box config (default scenario)."""
    logging.basicConfig(level=logging.WARNING - debug * 10)
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"[Ошибка] Не удалось загрузить конфиг: {e}", err=True)
        raise typer.Exit(1)

    exclusions = load_exclusions(dry_run=dry_run)
    indices = []
    if index:
        indices = [int(i) for i in index.split(",") if i.strip().isdigit()]
    else:
        saved_config = load_selected_config()
        indices = [int(item["index"]) for item in saved_config["selected"] if "index" in item]

    outbounds, excluded_ips, selected_servers = prepare_selection(
        json_data,
        indices,
        remarks,
        SUPPORTED_PROTOCOLS,
        exclusions,
        debug_level=debug,
        dry_run=dry_run
    )

    if (remarks or indices) and not dry_run and selected_servers:
        save_selected_config({"selected": selected_servers})

    # Определяем актуальные пути
    template_file = template_file or os.getenv("SBOXMGR_TEMPLATE_FILE", "./config.template.json")
    config_file = config_file or os.getenv("SBOXMGR_CONFIG_FILE", "/etc/sboxmgr/config.json")
    backup_file = backup_file or os.getenv("SBOXMGR_BACKUP_FILE", "/etc/sboxmgr/config.json.bak")

    if dry_run:
        from sboxmgr.config.generate import generate_temp_config, validate_config_file
        import tempfile
        typer.echo("Режим dry-run: создаём временный конфиг и валидируем его")
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            config_content = generate_temp_config(outbounds, template_file, excluded_ips)
            tmp.write(config_content)
        valid, output = validate_config_file(temp_path)
        if valid:
            typer.echo("Dry run: config is valid")
        else:
            typer.echo(f"Конфиг невалиден:\n{output}", err=True)
        os.unlink(temp_path)
        typer.echo("Временный файл удалён. Основной конфиг не изменён, сервис не перезапущен.")
        raise typer.Exit(0 if valid else 1)

    try:
        changes_made = generate_config(outbounds, template_file, config_file, backup_file, excluded_ips)
        if changes_made:
            try:
                manage_service()
                if debug >= 1:
                    typer.echo("Service restart completed.")
            except Exception as e:
                if os.environ.get("MOCK_MANAGE_SERVICE") == "1":
                    typer.echo("[Info] manage_service mock: ignoring error and exiting with code 0")
                    raise typer.Exit(0)
                else:
                    raise
    except Exception as e:
        typer.echo(f"Error during config update: {e}", err=True)
        raise typer.Exit(1)

    typer.echo("=== Update completed successfully ===")

@app.command()
def dry_run(
    url: str = typer.Option(
        ..., "-u", "--url", help="Config subscription URL",
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    remarks: str = typer.Option(None, "-r", "--remarks", help="Select server by remarks"),
    index: str = typer.Option(None, "-i", "--index", help="Select server by index (comma-separated)"),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug level: 0=min, 1=info, 2=debug"),
    config_file: str = typer.Option(None, "--config-file", help="Path to config.json (overrides env)"),
    template_file: str = typer.Option(None, "--template-file", help="Path to config.template.json (overrides env)"),
):
    """Validate config and print result (no changes)."""
    logging.basicConfig(level=logging.WARNING - debug * 10)
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"[Ошибка] Не удалось загрузить конфиг: {e}", err=True)
        raise typer.Exit(1)

    exclusions = load_exclusions(dry_run=True)
    indices = []
    if index:
        indices = [int(i) for i in index.split(",") if i.strip().isdigit()]
    else:
        saved_config = load_selected_config()
        indices = [int(item["index"]) for item in saved_config["selected"] if "index" in item]

    outbounds, excluded_ips, selected_servers = prepare_selection(
        json_data,
        indices,
        remarks,
        SUPPORTED_PROTOCOLS,
        exclusions,
        debug_level=debug,
        dry_run=True
    )

    # Определяем актуальные пути
    template_file = template_file or os.getenv("SBOXMGR_TEMPLATE_FILE", "./config.template.json")
    config_file = config_file or os.getenv("SBOXMGR_CONFIG_FILE", "/etc/sboxmgr/config.json")

    from sboxmgr.config.generate import generate_temp_config, validate_config_file
    import tempfile
    typer.echo("Режим dry-run: создаём временный конфиг и валидируем его")
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        temp_path = tmp.name
        config_content = generate_temp_config(outbounds, template_file, excluded_ips)
        tmp.write(config_content)
    valid, output = validate_config_file(temp_path)
    if valid:
        typer.echo("Dry run: config is valid")
    else:
        typer.echo(f"Конфиг невалиден:\n{output}", err=True)
    os.unlink(temp_path)
    typer.echo("Временный файл удалён. Основной конфиг не изменён, сервис не перезапущен.")
    raise typer.Exit(0 if valid else 1)

@app.command("list-servers")
def list_servers(
    url: str = typer.Option(
        ..., "-u", "--url", help="Config subscription URL",
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug level: 0=min, 1=info, 2=debug"),
):
    """List all available servers from config."""
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"[Ошибка] Не удалось загрузить конфиг: {e}", err=True)
        raise typer.Exit(1)
    do_list_servers(json_data, SUPPORTED_PROTOCOLS, debug_level=debug, dry_run=True)

@app.command()
def exclusions(
    url: str = typer.Option(
        ..., "-u", "--url", help="Config subscription URL",
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    add: str = typer.Option(None, "--add", help="Add exclusions (comma-separated indices or names)"),
    remove: str = typer.Option(None, "--remove", help="Remove exclusions (comma-separated indices or names)"),
    view: bool = typer.Option(False, "--view", help="View current exclusions"),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug level: 0=min, 1=info, 2=debug"),
):
    """Manage exclusions: add, remove, view."""
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"[Ошибка] Не удалось загрузить конфиг: {e}", err=True)
        raise typer.Exit(1)
    if view:
        view_exclusions(debug)
        raise typer.Exit(0)
    if add:
        add_exclusions = [x.strip() for x in add.split(",") if x.strip()]
        exclude_servers(json_data, add_exclusions, SUPPORTED_PROTOCOLS, debug)
    if remove:
        remove_exclusions_list = [x.strip() for x in remove.split(",") if x.strip()]
        remove_exclusions(remove_exclusions_list, json_data, SUPPORTED_PROTOCOLS, debug)
    if not (add or remove or view):
        typer.echo("[Info] Use --add, --remove или --view для управления exclusions.")

@app.command("clear-exclusions")
def clear_exclusions(
    confirm: bool = typer.Option(False, "--yes", help="Confirm clearing exclusions"),
    debug: int = typer.Option(0, "-d", "--debug", help="Debug level: 0=min, 1=info, 2=debug"),
):
    """Clear all exclusions."""
    from sboxmgr.server.exclusions import clear_exclusions as do_clear_exclusions
    if not confirm:
        typer.echo("[Warning] Use --yes to confirm clearing all exclusions.")
        raise typer.Exit(1)
    do_clear_exclusions(debug)
    typer.echo("All exclusions cleared.")

if __name__ == "__main__":
    app() 