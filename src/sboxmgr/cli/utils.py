import json
import os
from pathlib import Path
import locale
import logging

def is_ai_lang(code):
    """Check if language file contains AI-generated translations.
    
    Examines the language file's metadata to determine if it contains
    AI-generated translations that may need human review and improvement.
    
    Args:
        code: Language code to check (e.g., 'en', 'ru', 'de').
        
    Returns:
        True if the language file is marked as AI-generated in its metadata,
        False otherwise or if the file doesn't exist.
    """
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
    """Detect current language setting and its configuration source.
    
    Determines the active language code by checking configuration sources
    in priority order: environment variable, config file, system locale,
    and finally default fallback.
    
    Returns:
        Tuple containing:
        - Language code string (e.g., 'en', 'ru', 'de')
        - Source description string indicating where the setting came from
        
    Note:
        Priority order:
        1. SBOXMGR_LANG environment variable
        2. default_lang in ~/.sboxmgr/config.toml
        3. System locale (LANG environment variable)  
        4. Default fallback ('en')
    """
    config_path = Path.home() / ".sboxmgr" / "config.toml"
    if os.environ.get("SBOXMGR_LANG"):
        return os.environ["SBOXMGR_LANG"], "env (SBOXMGR_LANG)"
    if config_path.exists():
        try:
            import toml
            cfg = toml.load(config_path)
            if "default_lang" in cfg:
                return cfg["default_lang"], f"config ({config_path})"
        except Exception as e:
            logging.debug(f"Failed to read config file {config_path}: {e}")
    try:
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang:
            return sys_lang.split("_")[0], "system LANG"
    except Exception as e:
        # Обрабатываем возможные исключения при работе с locale
        logging.debug(f"Failed to detect system locale: {e}")
    return "en", "default" 