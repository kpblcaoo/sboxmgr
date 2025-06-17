# Changelog

## [1.3.1] — 2024-06-18

### Added
- Полная автоматизация тестирования CLI: exclusions, clear-exclusions, идемпотентность, обработка ошибок, user-friendly сообщения, dry-run, selected_config.json, --list-servers, выбор excluded.
- User-friendly обработка ошибок при невалидном URL, повреждённом exclusions.json, попытке выбрать excluded сервер.
- Логирование ключевых CLI-действий и ошибок.

### Changed
- exclusions.json теперь хранит только SHA256-хеши id, а для пользователя — человекочитаемое поле name.
- selected_config.json не создаётся и не изменяется в режиме --dry-run.
- Улучшен CLI-вывод при повторном исключении сервера (информативное сообщение вместо дублирования).
- clear-exclusions теперь гарантированно удаляет exclusions.json вне зависимости от наличия URL.

### Fixed
- Исправлена идемпотентность exclusions: повторное добавление не дублирует записи.
- Исправлена обработка повреждённого exclusions.json (user-friendly сброс).
- Исправлена обработка невалидного URL (ошибка и returncode 1).
- Исправлены все баги, выявленные ручным и автоматическим тестированием CLI.

### Refactored
- Проведён рефакторинг структуры проекта: код перенесён в src/, декомпозиция крупных модулей, обновлены импорты.
- Улучшена модульность и читаемость кода, подготовка к автотестам.

### Testing
- Весь CLI покрыт автотестами (pytest), ручной чеклист полностью автоматизирован.
- Покрытие тестами — 100% по ключевым сценариям CLI.

---

> Некоторые экспериментальные фичи (например, install wizard) пока не документируются официально и будут представлены в следующих релизах.

## [v1.3.0] - 2025-05-16

### Added:
- Installer script (`install_update_singbox.sh`) to install the script to `/usr/local/bin/`, set up a systemd service, and configure a timer.
- Dynamic exclusion of servers from routing rules by IP using `ip_cidr` in the configuration template.

### Changed:
- Updated `config.template.json` to include a placeholder for `$excluded_servers` in the `ip_cidr` field.
- Enhanced script logic to replace the placeholder with actual IPs to be routed directly.

### Fixed:
- Ensured that specified IPs are routed directly, bypassing the proxy.

### Closed Issues:
- Issue #2: Implemented installer and enhanced exclusion logic.

---

## [v1.2.1] - 2025-05-16

### Fixed:
- Improved output for `-e` and `-l` options to work without verbosity.
- Allowed `-e` to function without `-u` when viewing exclusions.
- Handled missing `-u` option gracefully to prevent exceptions.
- Included server tags in the exclusions list.
- Corrected display of server ports in the server listing.
- Filtered out non-supported outbound types from the server list.
- Ensured server index numbers start at 0 and match the `-i` index.

---

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

### Known Issues:
 - -e and -l options produce no output unless verbosity is set (-d 1 or higher).
 - -e without an index should work even without -u <url>, but currently doesn't.
 - Server tags are not included in the exclusions list.
 - Server ports still display as N/A in some cases.
 - Non-supported outbound types appear in the server list.
 - Server index numbers do not start at 0 and may not match the -i index used for exclusion.


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
