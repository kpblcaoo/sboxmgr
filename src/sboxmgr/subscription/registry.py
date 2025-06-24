from typing import Type, Dict
import logging

PLUGIN_REGISTRY: Dict[str, Type] = {}

# Явная регистрация через декоратор

def register(source_type: str):
    def wrapper(cls):
        PLUGIN_REGISTRY[source_type] = cls
        return cls
    return wrapper

# Получение класса по типу

def get_plugin(source_type: str):
    return PLUGIN_REGISTRY.get(source_type)

# Задел под entry points (setuptools)
def load_entry_points():
    try:
        import importlib.metadata
        eps = importlib.metadata.entry_points()
        for ep in eps.select(group="sboxmgr.plugins"):  # group name по соглашению
            PLUGIN_REGISTRY[ep.name] = ep.load()
    except Exception as e:
        # entry points optional, не критично для MVP
        logging.debug(f"Failed to load entry points: {e}") 