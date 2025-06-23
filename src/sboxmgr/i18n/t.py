from .loader import LanguageLoader
import os
from functools import lru_cache

@lru_cache()
def current_lang() -> LanguageLoader:
    return LanguageLoader()

def t(key: str) -> str:
    return current_lang().get(key) 