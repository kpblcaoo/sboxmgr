# Инструкция по запуску тестов

## Установка зависимостей
Перед запуском тестов убедитесь, что все зависимости установлены:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
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
