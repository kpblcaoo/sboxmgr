import typer
import os
import sys
from dotenv import load_dotenv
from sboxmgr.config.fetch import fetch_json
from sboxmgr.utils.cli_common import prepare_selection
from sboxmgr.config.generate import generate_config
from sboxmgr.service.manage import manage_service
from sboxmgr.server.exclusions import load_exclusions, exclude_servers, remove_exclusions, view_exclusions
from sboxmgr.server.state import load_selected_config, save_selected_config
from sboxmgr.server.selection import list_servers as do_list_servers
from logsetup.setup import setup_logging
from sboxmgr.utils.env import get_log_file, get_config_file, get_backup_file, get_template_file, get_exclusion_file, get_selected_config_file, get_max_log_size, get_debug_level, get_url
from sboxmgr.subscription.manager import SubscriptionManager
from sboxmgr.subscription.models import SubscriptionSource, PipelineContext
from sboxmgr.i18n.loader import LanguageLoader
from pathlib import Path
import locale
from sboxmgr.i18n.t import t
from .plugin_template import plugin_template
from .commands.lang import lang_cmd
from .commands.subscription import run, dry_run, list_servers

load_dotenv()

lang = LanguageLoader(os.getenv('SBOXMGR_LANG', 'en'))

# Централизованное логирование для всех CLI-команд
LOG_FILE = get_log_file()
MAX_LOG_SIZE = get_max_log_size()
DEBUG_LEVEL = get_debug_level()
setup_logging(DEBUG_LEVEL, LOG_FILE, MAX_LOG_SIZE)

app = typer.Typer(help=lang.get("cli.help"))

SUPPORTED_PROTOCOLS = {"vless", "shadowsocks", "vmess", "trojan", "tuic", "hysteria2"}

def is_ai_lang(code):
    import json
    from pathlib import Path
    i18n_dir = Path(__file__).parent.parent / "i18n"
    lang_file = i18n_dir / f"{code}.json"
    if lang_file.exists():
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return "__note__" in data and "AI-generated" in data["__note__"]
        except Exception:
            return False
    return False

@app.command(help=t("cli.run.help"))
def run(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    remarks: str = typer.Option(None, "-r", "--remarks", help=t("cli.remarks.help")),
    index: str = typer.Option(None, "-i", "--index", help=t("cli.index.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    dry_run: bool = typer.Option(False, "--dry-run", help=t("cli.dry_run.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    backup_file: str = typer.Option(None, "--backup-file", help=t("cli.backup_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    use_selected: bool = typer.Option(False, "--use-selected", help=t("cli.use_selected.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """Generate and apply sing-box config (default scenario)."""
    try:
        # Определяем user_agent для SubscriptionSource
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base64", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=dry_run)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []  # TODO: добавить опции CLI для user_routes при необходимости
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
        if not config.success or not config.config or not config.config.get("outbounds"):
            typer.echo("ERROR: No servers parsed from subscription, config not updated.", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1)

    # Сохраняем/валидируем config как раньше
    template_file = template_file or get_template_file()
    config_file = config_file or get_config_file()
    backup_file = backup_file or get_backup_file()

    import json
    config_json = json.dumps(config.config, indent=2, ensure_ascii=False)

    if dry_run:
        from sboxmgr.config.generate import validate_config_file
        import tempfile
        typer.echo(lang.get("cli.dry_run_mode"))
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            temp_path = tmp.name
            tmp.write(config_json)
        valid, output = validate_config_file(temp_path)
        if valid:
            typer.echo(lang.get("cli.dry_run_valid"))
        else:
            typer.echo(f"{lang.get('cli.config_invalid')}\n{output}", err=True)
        os.unlink(temp_path)
        typer.echo(lang.get("cli.temp_file_deleted"))
        raise typer.Exit(0 if valid else 1)

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_json)
        # Бэкап
        if backup_file:
            import shutil
            shutil.copy2(config_file, backup_file)
        # Перезапуск сервиса
        try:
            manage_service()
            if debug >= 1:
                typer.echo(lang.get("cli.service_restart_completed"))
        except Exception as e:
            typer.echo(f"[WARN] Failed to restart sing-box.service: {e}", err=True)
            # Не завершаем выполнение с ошибкой, просто предупреждаем
    except Exception as e:
        typer.echo(f"{lang.get('cli.error_config_update')}: {e}", err=True)
        raise typer.Exit(1)

    typer.echo(lang.get("cli.update_completed"))

@app.command(help=t("cli.dry_run.help"))
def dry_run(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    remarks: str = typer.Option(None, "-r", "--remarks", help=t("cli.remarks.help")),
    index: str = typer.Option(None, "-i", "--index", help=t("cli.index.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    config_file: str = typer.Option(None, "--config-file", help=t("cli.config_file.help")),
    template_file: str = typer.Option(None, "--template-file", help=t("cli.template_file.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """Validate config and print result (no changes)."""
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base4", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=True)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
        if not config.success or not config.config or not config.config.get("outbounds"):
            typer.echo("ERROR: No servers parsed from subscription, nothing to validate.", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1)

    import json
    config_json = json.dumps(config.config, indent=2, ensure_ascii=False)
    from sboxmgr.config.generate import validate_config_file
    import tempfile
    typer.echo(lang.get("cli.dry_run_mode"))
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
        temp_path = tmp.name
        tmp.write(config_json)
    valid, output = validate_config_file(temp_path)
    if valid:
        typer.echo(lang.get("cli.dry_run_valid"))
    else:
        typer.echo(f"{lang.get('cli.config_invalid')}\n{output}", err=True)
    os.unlink(temp_path)
    typer.echo(lang.get("cli.temp_file_deleted"))
    raise typer.Exit(0 if valid else 1)

@app.command("list-servers", help=t("cli.list_servers.help"))
def list_servers(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    user_agent: str = typer.Option(None, "--user-agent", help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)"),
    no_user_agent: bool = typer.Option(False, "--no-user-agent", help="Do not send User-Agent header at all")
):
    """List all available servers from config."""
    try:
        if no_user_agent:
            ua = ""
        else:
            ua = user_agent
        source = SubscriptionSource(url=url, source_type="url_base64", user_agent=ua)
        mgr = SubscriptionManager(source)
        exclusions = load_exclusions(dry_run=True)
        context = PipelineContext(mode="default", debug_level=debug)
        user_routes = []
        config = mgr.export_config(exclusions=exclusions, user_routes=user_routes, context=context)
        # Защита от None
        if not config.config or not isinstance(config.config, dict):
            typer.echo("[Error] No valid config generated from subscription.", err=True)
            raise typer.Exit(1)
        servers = config.config.get("outbounds", [])
        for i, s in enumerate(servers):
            typer.echo(f"[{i}] {s.get('tag', s.get('server', ''))} ({s.get('type', '')}:{s.get('server_port', '')})")
    except Exception as e:
        typer.echo(f"{lang.get('error.subscription_failed')}: {e}", err=True)
        raise typer.Exit(1)

@app.command(help=t("cli.exclusions.help"))
def exclusions(
    url: str = typer.Option(
        ..., "-u", "--url", help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"]
    ),
    add: str = typer.Option(None, "--add", help=t("cli.add.help")),
    remove: str = typer.Option(None, "--remove", help=t("cli.remove.help")),
    view: bool = typer.Option(False, "--view", help=t("cli.view.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
):
    """Manage exclusions: add, remove, view."""
    try:
        json_data = fetch_json(url)
    except Exception as e:
        typer.echo(f"{lang.get('error.config_load_failed')}: {e}", err=True)
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
        typer.echo(lang.get("cli.use_add_remove_view"))

@app.command("clear-exclusions", help=t("cli.clear_exclusions.help"))
def clear_exclusions(
    confirm: bool = typer.Option(False, "--yes", help=t("cli.confirm.help")),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
):
    """Clear all exclusions."""
    from sboxmgr.server.exclusions import clear_exclusions as do_clear_exclusions
    if not confirm:
        typer.echo("[Warning] Use --yes to confirm clearing all exclusions.")
        raise typer.Exit(1)
    do_clear_exclusions()
    typer.echo("All exclusions cleared.")

@app.command("lang")
def lang_cmd(
    set_lang: str = typer.Option(None, "--set", "-s", help=lang.get_with_fallback("cli.lang.set.help")),
    check: bool = typer.Option(False, "--check", help=lang.get_with_fallback("cli.lang.check.help")),
):
    """
    Manage CLI language (i18n): show current, list available, set and persist language.
    """
    config_path = Path.home() / ".sboxmgr" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    def detect_lang_source():
        if os.environ.get("SBOXMGR_LANG"):
            return os.environ["SBOXMGR_LANG"], "env (SBOXMGR_LANG)"
        if config_path.exists():
            try:
                import toml
                cfg = toml.load(config_path)
                if "default_lang" in cfg:
                    return cfg["default_lang"], f"config ({config_path})"
            except Exception as e:
                typer.echo(f"[Warning] Failed to read {config_path}: {e}. Falling back to system LANG.", err=True)
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang:
            return sys_lang.split("_")[0], "system LANG"
        return "en", "default"

    if set_lang:
        loader = LanguageLoader()
        if not loader.exists(set_lang):
            typer.echo(f"Language '{set_lang}' not found in i18n folder.")
            typer.echo(f"Available: {', '.join(loader.list_languages())}")
            raise typer.Exit(1)
        try:
            import toml
            with open(config_path, "w") as f:
                toml.dump({"default_lang": set_lang}, f)
            typer.echo(f"Language set to '{set_lang}' and persisted in {config_path}.")
        except Exception as e:
            typer.echo(f"[Error] Failed to write config: {e}", err=True)
            raise typer.Exit(1)
    else:
        lang_code, source = detect_lang_source()
        loader = LanguageLoader(lang_code)
        typer.echo(f"Current language: {lang_code} (source: {source})")
        if source in ("system LANG", "default"):
            # Двуязычный вывод help и notice
            en_loader = LanguageLoader("en")
            local_loader = loader if lang_code != "en" else None
            typer.echo("--- English ---")
            typer.echo(en_loader.get("cli.lang.help"))
            typer.echo(en_loader.get("cli.lang.bilingual_notice"))
            if local_loader:
                typer.echo("--- Русский ---" if lang_code == "ru" else f"--- {lang_code.upper()} ---")
                typer.echo(local_loader.get("cli.lang.help"))
                typer.echo(local_loader.get("cli.lang.bilingual_notice"))
        else:
            typer.echo(loader.get("cli.lang.help"))
        # --- Вывод языков с самоназванием и пометками ---
        LANG_NAMES = {
            "en": "English",
            "ru": "Русский",
            "de": "Deutsch",
            "zh": "中文",
            "fa": "فارسی",
            "tr": "Türkçe",
            "uk": "Українська",
            "es": "Español",
            "fr": "Français",
            "ar": "العربية",
            "pl": "Polski",
        }
        langs = loader.list_languages()
        langs_out = []
        for code in langs:
            name = LANG_NAMES.get(code, code)
            ai = " [AI]" if is_ai_lang(code) else ""
            langs_out.append(f"  {code} - {name}{ai}")
        typer.echo("Available languages:")
        for l in langs_out:
            typer.echo(l)
        if any(is_ai_lang(code) for code in langs):
            typer.echo("Note: [AI] = machine-translated, not reviewed. Contributions welcome!")
        typer.echo(f"To set language persistently: sboxctl lang --set ru")
        typer.echo(f"Or for one-time use: SBOXMGR_LANG=ru sboxctl ...")

app.command("plugin-template")(plugin_template)
app.command()(run)
app.command()(dry_run)
app.command("list-servers")(list_servers)

if __name__ == "__main__":
    app() 