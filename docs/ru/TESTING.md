# Инструкция по запуску тестов

## Другие языки / Other languages
- [English (TESTING.md)](../TESTING.md)

## Установка зависимостей
Перед запуском тестов убедитесь, что все зависимости установлены:
```bash
python -m venv .venv
source .venv/bin/activate
pip install .[dev]
cp .env.example .env  # Отредактируйте при необходимости
```

## Запуск тестов
Для запуска всех тестов выполните команду:
```bash
pytest
```

## Проверка покрытия тестов
Для проверки покрытия кода выполните:
```bash
pytest --cov=. --cov-report=term-missing
```

## Структура тестов
- Тесты находятся в папке `tests/`.
- Каждый модуль имеет соответствующий файл тестов, например:
  - `config_fetch.py` -> `tests/test_config_fetch.py`
  - `protocol_validation.py` -> `tests/test_protocol_validation.py`.
