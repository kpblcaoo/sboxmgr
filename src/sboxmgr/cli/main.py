import typer
import os
from dotenv import load_dotenv
from sboxmgr.config.fetch import fetch_json
from sboxmgr.server.exclusions import exclude_servers, remove_exclusions, view_exclusions
from logsetup.setup import setup_logging
from sboxmgr.utils.env import get_log_file, get_max_log_size, get_debug_level
from sboxmgr.i18n.loader import LanguageLoader
from pathlib import Path
import locale
from sboxmgr.i18n.t import t
from sboxmgr.cli import plugin_template
from sboxmgr.cli.commands.config import config_app

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
    """Check if language is AI-generated based on metadata.
    
    Examines the language file's metadata to determine if it contains
    AI-generated translations that may need human review.
    
    Args:
        code: Language code to check (e.g., 'en', 'ru', 'de').
        
    Returns:
        True if language is marked as AI-generated, False otherwise.
    """
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
    """Manage server exclusions for subscription filtering.
    
    Provides functionality to add, remove, and view server exclusions
    for subscription-based proxy configurations. Exclusions are persistent
    and apply to all subscription processing operations.
    
    Args:
        url: Subscription URL to fetch server list from.
        add: Comma-separated list of servers to exclude.
        remove: Comma-separated list of servers to remove from exclusions.
        view: Display current exclusions without modification.
        debug: Debug verbosity level (0-2).
        
    Raises:
        typer.Exit: On configuration load failure or invalid operations.
    """
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
    """Clear all server exclusions with confirmation.
    
    Removes all exclusion entries from the exclusion database. This operation
    is irreversible and requires explicit confirmation via the --yes flag
    for safety.
    
    Args:
        confirm: Explicit confirmation flag to proceed with clearing.
        debug: Debug verbosity level (0-2).
        
    Raises:
        typer.Exit: If confirmation is not provided.
    """
    from sboxmgr.server.exclusions import clear_exclusions as do_clear_exclusions
    if not confirm:
        typer.echo("[Warning] Use --yes to confirm clearing all exclusions.")
        raise typer.Exit(1)
    do_clear_exclusions()
    typer.echo("All exclusions cleared.")

@app.command("lang")
def lang_cmd(
    set_lang: str = typer.Option(None, "--set", "-s", help=lang.get_with_fallback("cli.lang.set.help")),
):
    """Manage CLI internationalization language settings.
    
    Provides language management functionality including displaying current
    language, listing available languages, and persistently setting the
    preferred language for CLI output.
    
    The language priority is:
    1. SBOXMGR_LANG environment variable
    2. Configuration file setting (~/.sboxmgr/config.toml)
    3. System locale (LANG)
    4. Default (English)
    
    Args:
        set_lang: Language code to set as default (e.g., 'en', 'ru', 'de').
        check: Display current language information without modification.
        
    Raises:
        typer.Exit: If specified language is not available or config write fails.
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
        for lang_line in langs_out:
            typer.echo(lang_line)
        if any(is_ai_lang(code) for code in langs):
            typer.echo("Note: [AI] = machine-translated, not reviewed. Contributions welcome!")
        typer.echo("To set language persistently: sboxctl lang --set ru")
        typer.echo("Or for one-time use: SBOXMGR_LANG=ru sboxctl ...")

app.command("plugin-template")(plugin_template.plugin_template)

# Регистрируем команды из commands/subscription.py
from sboxmgr.cli.commands.subscription import run as subscription_run, dry_run as subscription_dry_run, list_servers as subscription_list_servers
app.command("run", help=t("cli.run.help"))(subscription_run)
app.command()(subscription_dry_run) 
app.command("list-servers", help=t("cli.list_servers.help"))(subscription_list_servers)

# Регистрируем новую команду exclusions_v2
from sboxmgr.cli.commands.exclusions_v2 import exclusions_v2
app.command("exclusions-v2")(exclusions_v2)

# Регистрируем config команды
app.add_typer(config_app)

if __name__ == "__main__":
    app() 