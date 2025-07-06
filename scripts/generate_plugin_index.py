#!/usr/bin/env python3
"""
Автоматическая генерация docs/plugins/index.md по зарегистрированным плагинам.

Usage:
    python scripts/generate_plugin_index.py

Собирает все плагины из PLUGIN_REGISTRY, группирует по plugin_type, формирует markdown-таблицу с именем класса, типом, docstring и путём к файлу.
SEC: Импортируются только известные модули из src/sboxmgr/subscription/*, сторонние/неизвестные модули не импортируются.
"""
import inspect
import os

from sboxmgr.subscription.registry import PLUGIN_REGISTRY

# SEC: Импортируем только известные модули с плагинами (без динамики)

# Собираем плагины по типу
plugins_by_type = {}
for name, cls in PLUGIN_REGISTRY.items():
    ptype = getattr(cls, "plugin_type", "unknown")
    plugins_by_type.setdefault(ptype, []).append((name, cls))

rows = ["| Тип | Класс | Docstring | Файл |", "|------|--------|-----------|------|"]
for plugin_type, items in sorted(plugins_by_type.items()):
    for name, cls in items:
        doc = inspect.getdoc(cls) or ""
        try:
            file = inspect.getfile(cls)
            file = os.path.relpath(file, start=os.path.dirname(__file__))
        except Exception:
            file = "?"
        rows.append(
            f"| {plugin_type} | `{cls.__name__}` | {doc.splitlines()[0] if doc else ''} | `{file}` |"
        )

index_md = (
    """# Индекс зарегистрированных плагинов\n\nАвтоматически сгенерировано. Не редактируйте вручную!\n\n"""
    + "\n".join(rows)
    + "\n"
)

os.makedirs(os.path.join(os.path.dirname(__file__), "../docs/plugins"), exist_ok=True)
with open(
    os.path.join(os.path.dirname(__file__), "../docs/plugins/index.md"),
    "w",
    encoding="utf-8",
) as f:
    f.write(index_md)
