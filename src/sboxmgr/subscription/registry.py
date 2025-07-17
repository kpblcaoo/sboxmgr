"""Plugin registry for subscription parsers and exporters."""

import logging

PLUGIN_REGISTRY: dict[str, type] = {}

# Явная регистрация через декоратор


def register(source_type: str):
    """Register a plugin class for a specific source type.

    Args:
        source_type: Type of subscription source

    """

    def wrapper(cls):
        PLUGIN_REGISTRY[source_type] = cls
        return cls

    return wrapper


# Получение класса по типу


def get_plugin(source_type: str):
    """Get plugin class for a specific source type.

    Args:
        source_type: Type of subscription source

    Returns:
        Plugin class or None if not found

    """
    return PLUGIN_REGISTRY.get(source_type)


# Задел под entry points (setuptools)
def load_entry_points():
    """Load plugins from setuptools entry points."""
    try:
        import importlib.metadata

        eps = importlib.metadata.entry_points()
        for ep in eps.select(group="sboxmgr.plugins"):  # group name по соглашению
            PLUGIN_REGISTRY[ep.name] = ep.load()
    except Exception as e:
        # entry points optional, не критично для MVP
        logging.debug(f"Failed to load entry points: {e}")
