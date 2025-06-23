import json
import os
from pathlib import Path
import locale

def is_ai_lang(code):
    """Check if the language file is AI-generated."""
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

def detect_lang_source():
    """Detect the current language and its source (env, config, system)."""
    config_path = Path.home() / ".sboxmgr" / "config.toml"
    if os.environ.get("SBOXMGR_LANG"):
        return os.environ["SBOXMGR_LANG"], "env (SBOXMGR_LANG)"
    if config_path.exists():
        try:
            import toml
            cfg = toml.load(config_path)
            if "default_lang" in cfg:
                return cfg["default_lang"], f"config ({config_path})"
        except Exception:
            pass
    sys_lang = locale.getdefaultlocale()[0]
    if sys_lang:
        return sys_lang.split("_")[0], "system LANG"
    return "en", "default" 