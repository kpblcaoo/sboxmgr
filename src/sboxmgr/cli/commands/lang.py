import typer
from pathlib import Path
from sboxmgr.i18n.loader import LanguageLoader
from ..utils import is_ai_lang, detect_lang_source
import locale
import os

lang = LanguageLoader(os.getenv('SBOXMGR_LANG', 'en'))

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

def lang_cmd(
    set_lang: str = typer.Option(None, "--set", "-s", help=lang.get_with_fallback("cli.lang.set.help")),
    check: bool = typer.Option(False, "--check", help=lang.get_with_fallback("cli.lang.check.help")),
):
    """
    Manage CLI language (i18n): show current, list available, set and persist language.
    """
    config_path = Path.home() / ".sboxmgr" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

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