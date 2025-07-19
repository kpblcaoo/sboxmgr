# CLI Documentation Generator

Автоматический генератор документации для CLI команд SboxMgr.

## Возможности

- ✅ **Автоматическое обнаружение** всех команд и подкоманд
- ✅ **Рекурсивный парсинг** help-выводов
- ✅ **Markdown форматирование** с эмодзи и структурированными заголовками
- ✅ **Гибкие опции вывода** (файл, stdout)
- ✅ **Поддержка --show-details** для расширенной документации
- ✅ **Статистика команд** и обзор групп
- ✅ **Кеширование** для оптимизации производительности

## Использование

### Базовое использование
```bash
# Генерация в tmp/cli_dump.md
python scripts/dump_cli_commands.py

# Генерация в конкретный файл
python scripts/dump_cli_commands.py --output docs/cli/reference.md

# Вывод в stdout
python scripts/dump_cli_commands.py --output -
```

### Расширенные опции
```bash
# С подробной документацией (если поддерживается)
python scripts/dump_cli_commands.py --show-details

# Комбинация опций
python scripts/dump_cli_commands.py --output docs/cli/full.md --show-details
```

## Примеры вывода

### Структура документации
```markdown
# SboxMgr CLI Commands Reference

## 🔹 Main CLI Help
[main help output]

## 🔹 Command: `sboxctl profile`
[profile help output]

### 🔸 Subcommand: `sboxctl profile list`
[profile list help output]

---

# 📊 CLI Commands Statistics
- **Total main commands**: 11
- **Total subcommands**: 37
- **Total commands**: 48
```

### Статистика команд
```markdown
## Command Groups Overview
- **`sboxctl config`**: 8 subcommands
- **`sboxctl profile`**: 8 subcommands
- **`sboxctl export`**: 3 subcommands
- **`sboxctl policy`**: 6 subcommands
```

## Технические детали

### Парсинг команд
- Использует robust парсинг для Click-Rich CLI
- Валидация через `isidentifier()` для корректных имен команд
- Обработка многострочных описаний

### Оптимизация
- Кеширование `main_help` для избежания дублирования вызовов
- Эффективный парсинг help-выводов
- Минимальные зависимости (только stdlib)

### Форматирование
- Эмодзи для визуального разделения
- Структурированные заголовки с полными путями команд
- Разделители между подкомандами

## Интеграция

### В CI/CD
```yaml
# .github/workflows/docs.yml
- name: Generate CLI docs
  run: python scripts/dump_cli_commands.py --output docs/cli/reference.md
```

### В Makefile
```makefile
docs/cli/reference.md: scripts/dump_cli_commands.py
	python scripts/dump_cli_commands.py --output $@
```

## Разработка

### Добавление новых опций
1. Добавить аргумент в `argparse`
2. Передать флаг в `dump_command_tree()`
3. Обновить функции `get_*_help()`

### Улучшение парсинга
- Модифицировать `extract_subcommands()`
- Добавить тесты для edge cases
- Проверить совместимость с новыми CLI фреймворками

## Лицензия

Часть проекта SboxMgr. См. LICENSE в корне проекта.
