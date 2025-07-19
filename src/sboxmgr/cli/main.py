"""Main CLI entry point for sboxctl command-line interface.

This module defines the root Typer application and registers all CLI command
groups (subscription, exclusions, lang, etc.). It serves as the primary entry
point for the `sboxctl` console script defined in pyproject.toml.
"""

import locale
import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from sboxmgr.cli import plugin_template
from sboxmgr.cli.commands.config import app as new_config_app
from sboxmgr.cli.commands.export_v2 import app as export_v2_app
from sboxmgr.cli.commands.policy import app as policy_app
from sboxmgr.cli.commands.profile import app as profile_app
from sboxmgr.cli.commands.subscription import app as subscription_app

# Import commands for registration
from sboxmgr.cli.commands.subscription.list import (
    list_servers as subscription_list_servers,
)
from sboxmgr.config.models import LoggingConfig
from sboxmgr.i18n.loader import LanguageLoader
from sboxmgr.i18n.t import t
from sboxmgr.logging import initialize_logging

load_dotenv()

# Initialize logging for CLI
logging_config = LoggingConfig(level="INFO", format="text", sinks=["stdout"])
initialize_logging(logging_config)

lang = LanguageLoader(os.getenv("SBOXMGR_LANG", "en"))

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
            with open(lang_file, encoding="utf-8") as f:
                data = json.load(f)
            return "__note__" in data and "AI-generated" in data["__note__"]
        except Exception:
            return False
    return False


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit",
        is_eager=True,
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompts and use default values",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose output with additional details",
    ),
    ctx: typer.Context = None,
):
    """Root callback to handle global options like --version, --yes, --verbose."""
    # Initialize context object for global flags
    if ctx is not None:
        ctx.ensure_object(dict)
        ctx.obj["yes"] = yes
        ctx.obj["verbose"] = verbose

    if version:
        try:
            from importlib.metadata import version as _version

            typer.echo(_version("sboxmgr"))
        except Exception:
            typer.echo("unknown")
        raise typer.Exit(0)


@app.command("lang")
def lang_cmd(
    set_lang: str = typer.Option(
        None, "--set", "-s", help=lang.get("cli.lang.set.help")
    ),
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
                typer.echo(
                    f"[Warning] Failed to read {config_path}: {e}. Falling back to system LANG.",
                    err=True,
                )
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
            typer.echo(f"❌ {t('cli.error.config_save_failed')}: {e}", err=True)
            raise typer.Exit(1) from e
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
                typer.echo(
                    "--- Русский ---"
                    if lang_code == "ru"
                    else f"--- {lang_code.upper()} ---"
                )
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
            typer.echo(
                "Note: [AI] = machine-translated, not reviewed. Contributions welcome!"
            )
        typer.echo("To set language persistently: sboxctl lang --set ru")
        typer.echo("Or for one-time use: SBOXMGR_LANG=ru sboxctl ...")


app.command("plugin-template")(plugin_template.plugin_template)


# Register deprecated commands as aliases (for backward compatibility)
# Note: These are hidden aliases that will be removed in future versions
@app.command("list-servers", hidden=True, help=t("cli.list_servers.help"))
def list_servers_alias(
    url: str = typer.Option(
        ...,
        "-u",
        "--url",
        help=t("cli.url.help"),
        envvar=["SBOXMGR_URL", "SINGBOX_URL", "TEST_URL"],
    ),
    debug: int = typer.Option(0, "-d", "--debug", help=t("cli.debug.help")),
    user_agent: Optional[str] = typer.Option(
        None,
        "--user-agent",
        help="Override User-Agent for subscription fetcher (default: ClashMeta/1.0)",
    ),
    no_user_agent: bool = typer.Option(
        False, "--no-user-agent", help="Do not send User-Agent header at all"
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        help="Force specific format: auto, base64, json, uri_list, clash",
    ),
    policy_details: bool = typer.Option(
        False,
        "-P",
        "--policy-details",
        help="Show policy evaluation details for each server",
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        help="Output format: table, json",
    ),
    ctx: typer.Context = None,
):
    """Alias for sboxctl subscription list (deprecated)."""
    typer.echo(t("cli.deprecated.list_servers"))
    # Call the original function with all parameters including context
    subscription_list_servers(
        url=url,
        debug=debug,
        user_agent=user_agent,
        no_user_agent=no_user_agent,
        format=format,
        policy_details=policy_details,
        output_format=output_format,
        ctx=ctx,
    )


# Регистрируем config команды
app.add_typer(new_config_app, name="config")

# Регистрируем subscription команды
app.add_typer(subscription_app, name="subscription")

# Регистрируем profile команды (ADR-0020)
app.add_typer(profile_app, name="profile")

# Регистрируем новую группу команд экспорта (ADR-0020)
app.add_typer(export_v2_app, name="export")


# Регистрируем команды политик
app.add_typer(policy_app)


@app.command("tui")
def tui_cmd(
    debug: int = typer.Option(
        0, "--debug", "-d", help="Debug level (0-3)", min=0, max=3
    ),
    profile: str = typer.Option(None, "--profile", "-p", help="Profile name to use"),
):
    """Launch Text User Interface (TUI) mode.

    Opens an interactive text-based interface for managing subscriptions
    and generating configurations. The TUI provides a user-friendly way
    to interact with sboxmgr without memorizing CLI commands.

    Features:
    - Context-aware interface that adapts to your current setup
    - Step-by-step onboarding for new users
    - Visual server management with exclusion controls
    - Real-time validation and error handling
    - Keyboard shortcuts for efficient navigation

    Args:
        debug: Debug level (0=off, 1=info, 2=verbose, 3=trace)
        profile: Profile name to use (defaults to current profile)

    Examples:
        sboxctl tui                    # Launch TUI with default settings
        sboxctl tui --debug 1          # Launch with debug info
        sboxctl tui --profile work     # Launch with specific profile

    """
    try:
        from sboxmgr.tui.app import SboxmgrTUI

        # Create and run the TUI application
        tui_app = SboxmgrTUI(debug=debug, profile=profile)
        tui_app.run()

    except ImportError as e:
        typer.echo(
            f"TUI dependencies not available: {e}\n"
            "Please install with: pip install textual>=0.52.0",
            err=True,
        )
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"TUI error: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
