# Справочник CLI команд

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

## Коды возврата

- `0` - успешное выполнение
- `1` - ошибка (файл не найден, невалидный профиль, etc.)
- `2` - ошибка синтаксиса командной строки

---

**См. также:**
- [Руководство по управлению профилями](guides/profile_management.md)
- [ADR-0017: Full Profile Architecture](../arch/decisions/ADR-0017-full-profile-architecture.md) 