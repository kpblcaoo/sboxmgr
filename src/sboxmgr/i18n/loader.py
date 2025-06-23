import json
from pathlib import Path
import os
import locale

class LanguageLoader:
    def __init__(self, lang: str = None, base_dir: Path = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        if lang is not None:
            self.lang = lang
            self.lang_source = "forced"
        else:
            self.lang, self.lang_source = self.get_preferred_lang_with_source()
        self.translations = {}
        self.en_translations = {}
        self.load()

    def load(self):
        file = self.base_dir / f"{self.lang}.json"
        en_file = self.base_dir / "en.json"
        if not file.exists() and self.lang != "en":
            print(f"[i18n] Language '{self.lang}' not found. Falling back to English (en).")
            print("To use another language, set SBOXMGR_LANG (e.g., 'SBOXMGR_LANG=ru sboxctl ...') or use 'sboxctl lang --set ru'.")
        try:
            raw = json.loads(file.read_text(encoding="utf-8"))
            self.translations = self.sanitize(raw)
        except Exception:
            self.translations = {}
        try:
            raw_en = json.loads(en_file.read_text(encoding="utf-8"))
            self.en_translations = self.sanitize(raw_en)
        except Exception:
            self.en_translations = {}

    def sanitize(self, mapping: dict) -> dict:
        # Удалить ANSI, ограничить длину, убрать подозрительное
        return {
            k: v.replace("\x1b", "").strip()[:500]
            for k, v in mapping.items()
            if isinstance(v, str)
        }

    def get(self, key: str) -> str:
        # Сначала ищем в локальном языке, затем в en, иначе возвращаем ключ
        return self.translations.get(key) or self.en_translations.get(key, key)

    def get_with_fallback(self, key: str) -> str:
        """
        Если язык не задан явно (source == 'default' или 'LANG'), возвращает оба варианта:
        [en] ...\n[ru] ...
        Иначе — только локальный перевод.
        """
        local = self.translations.get(key, None)
        en = self.en_translations.get(key, key)
        if self.lang_source in ("default", "LANG") and self.lang != "en" and local and local != en:
            return f"[en] {en}\n[{self.lang}] {local}"
        return local or en

    def exists(self, lang_code: str) -> bool:
        return (self.base_dir / f"{lang_code}.json").exists()

    def list_languages(self) -> list:
        return sorted([p.stem for p in self.base_dir.glob("*.json")])

    @staticmethod
    def get_preferred_lang_with_source() -> tuple:
        # 1. env
        lang = os.environ.get("SBOXMGR_LANG")
        if lang:
            return lang, "env"
        # 2. config
        config_path = Path.home() / ".sboxmgr" / "config.toml"
        if config_path.exists():
            try:
                import toml
                cfg = toml.load(config_path)
                if "default_lang" in cfg:
                    return cfg["default_lang"], "config"
            except Exception:
                pass
        # 3. system LANG
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang:
            return sys_lang.split("_")[0], "LANG"
        return "en", "default" 