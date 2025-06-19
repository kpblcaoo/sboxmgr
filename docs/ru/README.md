# update-singbox

## Другие языки / Other languages
- [English (README.md)](../../README.md)

Скрипт на Python для автоматизации обновления конфигураций [sing-box](https://sing-box.sagernet.org/), универсальной прокси-платформы. Инструмент загружает данные о прокси-серверах по указанному URL и применяет их к конфигурации sing-box, поддерживая различные протоколы и правила маршрутизации.

---

## ✨ Возможности
- Загрузка и применение конфигураций прокси-серверов с указанного URL
- Поддерживаемые протоколы: VLESS, Shadowsocks, VMess, Trojan, TUIC, Hysteria2
- Прямая маршрутизация для российских доменов и geoip-ru, остальной трафик через прокси
- Логирование, резервные копии, exclusions, dry-run, полное покрытие CLI тестами
- Все пути и артефакты настраиваются через переменные окружения
- Модульная архитектура, тестирование через pytest + Typer.CliRunner

---

## 🚀 Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env  # Отредактируйте при необходимости
```

Требования: Python 3.10+, sing-box, requests[socks], python-dotenv

---

## ⚙️ Использование

Все команды доступны через CLI `sboxctl` (на Typer):

```bash
sboxctl run -u https://example.com/proxy-config.json --index 1
sboxctl dry-run -u https://example.com/proxy-config.json
sboxctl list-servers -u https://example.com/proxy-config.json
sboxctl exclusions -u https://example.com/proxy-config.json --add 1
sboxctl exclusions -u https://example.com/proxy-config.json --remove 1
sboxctl clear-exclusions
```

### Опции
| Опция                  | Описание                                         |
|-----------------------|--------------------------------------------------|
| `-u, --url <URL>`     | URL конфигурации прокси (**обязательно**)        |
| `--index <n>`         | Выбор сервера по индексу                         |
| `--remarks <name>`    | Выбор сервера по имени (remarks)                 |
| `--dry-run`           | Симуляция генерации конфига, без изменений файлов|
| `--list-servers`      | Список всех доступных серверов                   |
| `--exclusions`        | Управление exclusions (добавить/удалить/список)  |
| `--clear-exclusions`  | Очистить exclusions                              |
| `-d, --debug <level>` | Уровень логирования (0=min, 1=info, 2=debug)     |

---

## 🧪 Тестирование

Запуск всех тестов:
```bash
pytest -v tests/
```

Вся логика CLI покрыта тестами с использованием Typer.CliRunner и pytest. Пути и артефакты изолируются через переменные окружения в тестах.

---

## 🛠 Конфигурация и переменные окружения

Все пути настраиваются через переменные окружения:

| Переменная                      | Значение по умолчанию         |
|---------------------------------|-------------------------------|
| `SBOXMGR_CONFIG_FILE`           | ./config.json                 |
| `SBOXMGR_TEMPLATE_FILE`         | ./config.template.json        |
| `SBOXMGR_LOG_FILE`              | ./sboxmgr.log                 |
| `SBOXMGR_EXCLUSION_FILE`        | ./exclusions.json             |
| `SBOXMGR_SELECTED_CONFIG_FILE`  | ./selected_config.json        |
| `SBOXMGR_URL`                   | (нет значения по умолчанию)   |

Для локальной разработки можно использовать файл `.env` в корне проекта.

**Примечание:** По умолчанию конфиг пишется в `/etc/sing-box/config.json` (дефолтная директория sing-box). Если ваша установка sing-box использует другой путь, задайте `SBOXMGR_CONFIG_FILE` в `.env`.

---

## 🤝 Вклад в проект

Любые улучшения приветствуются! Форкните репозиторий, внесите изменения и отправьте Pull Request.

---

## 📜 Лицензия

Проект распространяется под лицензией GNU GPL v3. Подробнее см. LICENSE. 