# Справочник CLI команд

## Обзор

`sboxmgr` - это инструмент для обработки подписок и генерации конфигураций. Согласно ADR-0015, sboxmgr фокусируется на обработке подписок и генерации конфигураций, а управление сервисами (запуск, остановка, перезапуск) выполняется отдельным агентом `sboxagent`.

### Основные принципы:
- **sboxmgr**: обработка подписок, генерация конфигураций, валидация
- **sboxagent**: управление сервисами, мониторинг, автообновления
- **Инсталлер**: установка системных зависимостей (sing-box, clash, wireguard)

## Профили (Profiles)

### `sboxmgr profile info <path>`

Показать краткую информацию о профиле.

**Аргументы:**
- `path` - путь к файлу профиля

**Пример:**
```bash
sboxmgr profile info /path/to/profile.json
```

**Вывод:**
```
Profile Info:
  Name: profile-name
  Path: /path/to/profile.json
  Size: 1024 bytes
  Modified: 2025-06-30 12:00:00
  Format: .json
  Sections: id, description, subscriptions, filters, routing, export, version
  Status: ✓ Valid
```

### `sboxmgr profile validate <path> [--normalize] [--verbose]`

Валидировать профиль.

**Аргументы:**
- `path` - путь к файлу профиля

**Опции:**
- `--normalize` - автоисправление профиля перед валидацией
- `--verbose` - подробный вывод

**Примеры:**
```bash
# Обычная валидация
sboxmgr profile validate /path/to/profile.json

# Валидация с автоисправлением
sboxmgr profile validate /path/to/profile.json --normalize

# Подробная валидация
sboxmgr profile validate /path/to/profile.json --verbose
```

### `sboxmgr profile apply <path> [--dry-run]`

Применить профиль.

**Аргументы:**
- `path` - путь к файлу профиля

**Опции:**
- `--dry-run` - показать что будет применено без фактического применения

**Примеры:**
```bash
# Применить профиль
sboxmgr profile apply /path/to/profile.json

# Показать что будет применено
sboxmgr profile apply /path/to/profile.json --dry-run
```

### `sboxmgr profile explain <path>`

Показать подробное объяснение структуры профиля.

**Аргументы:**
- `path` - путь к файлу профиля

**Пример:**
```bash
sboxmgr profile explain /path/to/profile.json
```

### `sboxmgr profile diff <path1> <path2>`

Сравнить два профиля.

**Аргументы:**
- `path1` - путь к первому профилю
- `path2` - путь ко второму профилю

**Пример:**
```bash
sboxmgr profile diff /path/to/profile1.json /path/to/profile2.json
```

### `sboxmgr profile list [--dir <directory>]`

Показать список доступных профилей.

**Опции:**
- `--dir` - директория для поиска профилей

**Примеры:**
```bash
# Список профилей в директории по умолчанию
sboxmgr profile list

# Список профилей в указанной директории
sboxmgr profile list --dir /path/to/profiles
```

### `sboxmgr profile switch <profile_id> [--dir <directory>]`

Переключиться на другой активный профиль.

**Аргументы:**
- `profile_id` - ID профиля (имя или путь)

**Опции:**
- `--dir` - директория для поиска профилей

**Примеры:**
```bash
# Переключиться на профиль по имени
sboxmgr profile switch dev

# Переключиться на профиль по пути
sboxmgr profile switch /path/to/profile.json
```

## Подписки (Subscriptions)

### `sboxmgr subscription orchestrated -u <url> [опции]`

Обновить конфигурацию из подписки с использованием Orchestrator.

**Аргументы:**
- `-u, --url` - URL подписки (обязательно)

**Опции:**
- `-d, --debug` - уровень отладки (0-2)
- `--dry-run` - проверить конфигурацию без сохранения
- `--config-file` - путь к выходному файлу конфигурации
- `--backup-file` - путь к файлу резервной копии
- `--user-agent` - пользовательский User-Agent
- `--no-user-agent` - отключить User-Agent
- `--format` - формат экспорта (singbox, clash, v2ray)
- `--user-routes` - теги маршрутов для включения (через запятую)
- `--exclusions` - серверы для исключения (через запятую)

**Примеры:**
```bash
# Базовое обновление
sboxmgr subscription orchestrated -u https://example.com/subscription

# С проверкой без изменений
sboxmgr subscription orchestrated -u https://example.com/subscription --dry-run

# С указанием выходного файла
sboxmgr subscription orchestrated -u https://example.com/subscription --config-file /etc/sing-box/config.json
```

**Примечание:** Эта команда только генерирует конфигурацию. Для применения изменений и перезапуска сервиса используйте `sboxagent`.

### `sboxmgr subscription list-servers -u <url> [опции]`

Показать список всех доступных серверов из подписки.

**Аргументы:**
- `-u, --url` - URL подписки (обязательно)

**Опции:**
- `-d, --debug` - уровень отладки (0-2)
- `--user-agent` - пользовательский User-Agent
- `--no-user-agent` - отключить User-Agent
- `--format` - принудительный формат (auto, base64, json, uri_list, clash)
- `-P, --policy-details` - показать детали политик для каждого сервера

**Примеры:**
```bash
# Список серверов
sboxmgr subscription list-servers -u https://example.com/subscription

# С деталями политик
sboxmgr subscription list-servers -u https://example.com/subscription --policy-details
```

## Экспорт (Export) - Phase 4 Integration

### `sboxmgr export [--profile <path>] [--validate-profile] [--profile-info]`

Экспорт конфигурации с поддержкой профилей.

**Опции:**
- `--profile` - путь к файлу профиля
- `--validate-profile` - валидировать профиль перед использованием
- `--profile-info` - показать информацию о профиле после экспорта

**Примеры:**
```bash
# Экспорт с использованием профиля
sboxmgr export --profile /path/to/profile.json

# Экспорт с валидацией профиля
sboxmgr export --profile /path/to/profile.json --validate-profile

# Экспорт с информацией о профиле
sboxmgr export --profile /path/to/profile.json --profile-info
```

## Исключения (Exclusions)

### `sboxmgr exclusions -u <url> [команды]`

Управление исключениями серверов.

**Аргументы:**
- `-u, --url` - URL подписки (обязательно)

**Команды:**
- `--add` - добавить исключения (индексы или имена через запятую)
- `--remove` - удалить исключения (индексы или имена через запятую)
- `--view` - просмотр текущих исключений
- `--clear` - очистить все исключения

**Примеры:**
```bash
# Добавить исключения
sboxmgr exclusions -u https://example.com/subscription --add "0,1,server-*" --reason "Testing"

# Просмотр исключений
sboxmgr exclusions -u https://example.com/subscription --view

# Очистить все исключения
sboxmgr exclusions -u https://example.com/subscription --clear
```

## Управление агентом

### `sboxmgr agent status`

Показать статус агента.

### `sboxmgr agent logs`

Показать логи агента.

### `sboxmgr agent config show`

Показать конфигурацию агента.

### `sboxmgr agent start/stop/restart`

Управление агентом.

**Примечание:** Эти команды управляют агентом `sboxagent`, который отвечает за применение конфигураций и управление сервисами.

## Коды возврата

- `0` - успешное выполнение
- `1` - ошибка (файл не найден, невалидный профиль, etc.)
- `2` - ошибка синтаксиса командной строки

## Миграция с предыдущих версий

### Изменения в управлении сервисами

В соответствии с ADR-0015, управление сервисами было вынесено в отдельный агент:

**Раньше:**
```bash
sboxmgr subscription orchestrated -u URL  # Автоматически перезапускал сервис
```

**Теперь:**
```bash
# Генерация конфигурации
sboxmgr subscription orchestrated -u URL

# Управление сервисом через агент
sboxmgr agent restart
```

### Установка агента

Для полной функциональности установите агент:

```bash
# Установка через curl
curl -sSL https://sbox.dev/install.sh | bash

# Или через sboxmgr
sboxmgr install agent
```

---

**См. также:**
- [Руководство по управлению профилями](guides/profile_management.md)
- [ADR-0015: Agent-Installer Separation](../arch/decisions/ADR-0015-agent-installer-separation.md)
- [Руководство по использованию агента](../AGENT_BRIDGE_USAGE.md) 