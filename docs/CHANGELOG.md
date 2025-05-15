# Changelog

## [v1.2.0] - 2025-05-15

### Added:
- Server exclusion and management features.
- Option to list servers with indices and details using `-l`.
- Ability to exclude servers by index or name with `-e`.
- Persistent storage for exclusions in `exclusions.json`.
- Option to view current exclusions.
- Option to clear all current exclusions with `--clear-exclusions`.

### Changed:
- Updated `list_servers` function to filter out inbounds and only list outbounds.
- Ensured configuration generation is triggered after server exclusions.

### Fixed:
- Corrected the display of server names and ports in the server listing.

---

## [v1.1.0] - 2025-05-14

### Added:
- Automatic server selection using `urltest` for latency-based routing.
- Rule actions in `route` section for DNS (`dns-out`) and private IP routing, replacing deprecated `block` and `dns` outbounds.

### Changed:
- Removed deprecated `block` and `dns` outbounds per `sing-box` 1.11.0 migration guide.
- Updated `config.template.json` to remove unsupported `default` field in `urltest` outbound.
- Fixed tests in `test_protocol_validation.py` and `test_config_generate.py` to align with current implementation.
- Updated `README.md` to reflect `urltest` usage and `sing-box` version requirements.

### Fixed:
- Resolved `ValueError: Unsupported protocol: None` in `test_protocol_validation.py` by using correct `type` field.
- Fixed `json.decoder.JSONDecodeError` in `test_config_generate.py` by using valid JSON template and proper mocking.

---

## [v1.0.0] - 2025-05-13

### Добавлено:
- Автоматическое тестирование с использованием `pytest`.
- Настроен CI/CD процесс с помощью GitHub Actions:
  - Workflow для тестирования в ветке `dev`.
  - Workflow для релиза в ветке `main`.
- Документация:
  - `DEVELOPMENT.md` с описанием процесса разработки.
  - `TESTING.md` с инструкцией по запуску тестов.

### Изменено:
- Улучшена структура проекта для поддержки тестирования и CI/CD.
- Перемещены модули в папку `modules/`:
  - `config_fetch.py`
  - `config_generate.py`
  - `protocol_validation.py`
  - `service_manage.py`
- Перемещена документация в папку `docs/`:
  - `README.md`
  - `CHANGELOG.md`
  - `DEVELOPMENT.md`
  - `TESTING.md`
- Тестовые файлы теперь используют `tests/config.json` вместо корневого `config.json`.

---

## [v0.3.0] - 2025-05-13

### Изменено:
- Скрипт `update_singbox.py` разделён на модули для улучшения читаемости, тестируемости и расширяемости.
  - `logging_setup.py`: Настройка логирования.
  - `config_fetch.py`: Загрузка и выбор конфигурации.
  - `protocol_validation.py`: Валидация протоколов и обработка настроек безопасности.
  - `config_generate.py`: Генерация и проверка конфигурации.
  - `service_manage.py`: Управление сервисом `sing-box`.

---

## [v0.2.3] - 2025-05-13

### Добавлено:
- Проверка изменений конфигурации перед её применением.
- Перезапуск сервиса `sing-box` только при наличии изменений.

---

## [v0.2.2] - 2025-05-12

### Добавлено:
- Уровни детализации логирования через флаг `--debug`:
  - `--debug 0`: Минимум логов (по умолчанию).
  - `--debug 1`: Информационные логи для ключевых действий.
  - `--debug 2`: Подробные логи для отладки.

---

## [v0.2.1] - 2025-05-12

### Изменено:
- Улучшение: Переписан процесс записи конфигурации. Теперь конфигурация сохраняется во временный файл, проверяется на валидность и только затем заменяет основной файл.
Это предотвращает возможные проблемы с повреждением основного конфигурационного файла.

---

## [v0.2.0] - 2025-05-11

### Добавлено
- Поддержка прокси (SOCKS и HTTP) для загрузки удалённых конфигураций.
- Начало ведения CHANGELOG.md!

### Изменено
- Перешёл с использования urllib на библиотеку requests для поддержки работы через прокси.

### Требования
- Добавлена новая зависимость: библиотека [requests](https://pypi.org/project/requests/). Убедитесь, что она установлена.

---

## [v0.1.0] - 2025-05-01 

### Добавлено
- Изначальная версия с поддержкой VLESS и Shadowsocks.