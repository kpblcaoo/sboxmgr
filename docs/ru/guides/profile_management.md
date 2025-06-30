# Руководство по управлению профилями

## Обзор

Система управления профилями в `sboxmgr` предоставляет мощные инструменты для создания, валидации и управления конфигурационными профилями. Профили позволяют сохранять и переключаться между различными настройками подписок, фильтров, экспорта и других компонентов.

## Структура профиля

Профиль представляет собой JSON файл со следующей структурой (согласно ADR-0017):

```json
{
  "id": "profile-name",
  "description": "Описание профиля",
  "subscriptions": [
    {
      "id": "sub-id",
      "enabled": true,
      "priority": 1
    }
  ],
  "filters": {
    "exclude_tags": ["slow"],
    "only_tags": ["premium"],
    "exclusions": [],
    "only_enabled": true
  },
  "routing": {
    "by_source": {},
    "default_route": "tunnel",
    "custom_routes": {}
  },
  "export": {
    "format": "sing-box",
    "outbound_profile": "vless-real",
    "inbound_profile": "tun",
    "output_file": "config.json"
  },
  "agent": {
    "auto_restart": false,
    "monitor_latency": true,
    "health_check_interval": "30s",
    "log_level": "info"
  },
  "ui": {
    "default_language": "ru",
    "mode": "cli",
    "theme": null,
    "show_debug_info": false
  },
  "version": "1.0"
}
```

## CLI команды

### Информация о профиле

```bash
# Показать краткую информацию о профиле
sboxmgr profile info /path/to/profile.json
```

Выводит:
- Имя и путь к файлу
- Размер и время изменения
- Список секций
- Статус валидности
- Ошибки (если есть)

### Валидация профиля

```bash
# Валидация профиля
sboxmgr profile validate /path/to/profile.json

# Валидация с автоисправлением
sboxmgr profile validate /path/to/profile.json --normalize

# Подробная валидация
sboxmgr profile validate /path/to/profile.json --verbose
```

Флаг `--normalize` автоматически исправляет:
- Конвертирует строки в списки для тегов
- Сохраняет существующие списки
- Обрабатывает отсутствующие секции

### Применение профиля

```bash
# Применить профиль
sboxmgr profile apply /path/to/profile.json

# Показать что будет применено (без применения)
sboxmgr profile apply /path/to/profile.json --dry-run
```

### Объяснение профиля

```bash
# Показать подробное объяснение структуры профиля
sboxmgr profile explain /path/to/profile.json
```

Выводит детальную информацию по каждой секции:
- Подписки с приоритетами и статусами
- Настройки экспорта
- Фильтры и исключения
- Маршрутизация
- Настройки агента и UI

### Сравнение профилей

```bash
# Сравнить два профиля
sboxmgr profile diff /path/to/profile1.json /path/to/profile2.json
```

Показывает:
- Общие секции
- Различия между секциями
- Секции только в одном из профилей

### Список профилей

```bash
# Список всех профилей в директории по умолчанию
sboxmgr profile list

# Список профилей в указанной директории
sboxmgr profile list --dir /path/to/profiles
```

### Переключение профиля

```bash
# Переключиться на профиль по имени
sboxmgr profile switch profile-name

# Переключиться на профиль по пути
sboxmgr profile switch /path/to/profile.json
```

## Секции профиля

### Subscriptions (Подписки)

Список конфигураций подписок:

```json
"subscriptions": [
  {
    "id": "premium-servers",
    "enabled": true,
    "priority": 1
  },
  {
    "id": "backup-servers", 
    "enabled": false,
    "priority": 2
  }
]
```

### Filters (Фильтры)

Настройки фильтрации серверов:

```json
"filters": {
  "exclude_tags": ["slow", "unstable"],
  "only_tags": ["premium", "fast"],
  "exclusions": ["blocked-server", "geo-restricted"],
  "only_enabled": true
}
```

### Export (Экспорт)

Настройки экспорта конфигурации:

```json
"export": {
  "format": "sing-box",
  "outbound_profile": "vless-real",
  "inbound_profile": "tun",
  "output_file": "/etc/sing-box/config.json",
  "template": "/path/to/custom/template.json"
}
```

Поддерживаемые форматы:
- `sing-box` - для sing-box
- `clash` - для Clash
- `json` - сырой JSON

### Routing (Маршрутизация)

Настройки маршрутизации:

```json
"routing": {
  "by_source": {
    "premium-servers": "tunnel",
    "backup-servers": "direct"
  },
  "default_route": "tunnel",
  "custom_routes": {
    "example.com": "direct",
    "*.google.com": "tunnel"
  }
}
```

### Agent (Агент)

Настройки агента:

```json
"agent": {
  "auto_restart": true,
  "monitor_latency": true,
  "health_check_interval": "30s",
  "log_level": "info"
}
```

### UI (Интерфейс)

Настройки пользовательского интерфейса:

```json
"ui": {
  "default_language": "ru",
  "mode": "cli",
  "theme": "dark",
  "show_debug_info": false
}
```

Поддерживаемые режимы:
- `cli` - командная строка
- `tui` - текстовый интерфейс
- `gui` - графический интерфейс

## Валидация и нормализация

### Автоматическая нормализация

Система может автоматически исправлять типичные ошибки:

```json
// До нормализации
"filters": {
  "exclude_tags": "slow",  // Строка
  "only_tags": "premium"   // Строка
}

// После нормализации
"filters": {
  "exclude_tags": ["slow"],  // Список
  "only_tags": ["premium"]   // Список
}
```

### Валидаторы секций

Каждая секция имеет специализированный валидатор:

- **SubscriptionSectionValidator** - проверяет подписки
- **ExportSectionValidator** - проверяет настройки экспорта
- **FilterSectionValidator** - проверяет фильтры

## Примеры использования

### Создание профиля для разработки

```json
{
  "id": "dev-profile",
  "description": "Профиль для разработки",
  "subscriptions": [
    {
      "id": "dev-servers",
      "enabled": true,
      "priority": 1
    }
  ],
  "filters": {
    "exclude_tags": ["production"],
    "only_tags": ["dev", "test"],
    "exclusions": [],
    "only_enabled": true
  },
  "export": {
    "format": "sing-box",
    "output_file": "/tmp/dev-config.json"
  },
  "ui": {
    "default_language": "en",
    "mode": "cli",
    "show_debug_info": true
  },
  "version": "1.0"
}
```

### Профиль для продакшена

```json
{
  "id": "prod-profile",
  "description": "Продакшен профиль",
  "subscriptions": [
    {
      "id": "prod-servers",
      "enabled": true,
      "priority": 1
    },
    {
      "id": "backup-servers",
      "enabled": true,
      "priority": 2
    }
  ],
  "filters": {
    "exclude_tags": ["dev", "test"],
    "only_tags": ["production", "stable"],
    "exclusions": ["unstable-server"],
    "only_enabled": true
  },
  "export": {
    "format": "sing-box",
    "output_file": "/etc/sing-box/config.json"
  },
  "agent": {
    "auto_restart": true,
    "monitor_latency": true,
    "health_check_interval": "60s",
    "log_level": "warn"
  },
  "version": "1.0"
}
```

## Интеграция с Phase 4

Профили интегрированы с системой экспорта (Phase 4):

```bash
# Экспорт с использованием профиля
sboxmgr export --profile /path/to/profile.json

# Экспорт с валидацией профиля
sboxmgr export --profile /path/to/profile.json --validate-profile

# Экспорт с информацией о профиле
sboxmgr export --profile /path/to/profile.json --profile-info
```

## Безопасность

### Валидация путей

Система проверяет безопасность путей:
- Запрещены пути к системным файлам (`/etc/passwd`, `/etc/shadow`)
- Проверка прав доступа к файлам
- Валидация шаблонов экспорта

### Контрольные суммы

Для будущих версий планируется:
- Автоматическое вычисление хешей профилей
- Проверка целостности при загрузке
- Подпись профилей

## Расширение системы

### Добавление новых валидаторов

```python
class CustomSectionValidator(ProfileSectionValidator):
    def validate(self, section_data: dict) -> list:
        errors = []
        # Ваша логика валидации
        return errors

# Регистрация в SECTION_VALIDATORS
SECTION_VALIDATORS['custom_section'] = CustomSectionValidator()
```

### Плагины для секций

Система поддерживает плагинную архитектуру для:
- Новых типов секций
- Кастомных валидаторов
- Расширенных нормализаторов

## Устранение неполадок

### Частые ошибки

1. **"Section 'subscriptions' must be a list"**
   - Убедитесь, что `subscriptions` это массив, а не объект

2. **"Filter exclude_tags must be a list"**
   - Используйте `--normalize` для автоисправления
   - Или исправьте вручную: `"exclude_tags": ["tag"]` вместо `"exclude_tags": "tag"`

3. **"Profile file not found"**
   - Проверьте путь к файлу
   - Убедитесь, что файл существует

### Отладка

```bash
# Подробная валидация
sboxmgr profile validate profile.json --verbose

# Объяснение структуры
sboxmgr profile explain profile.json

# Сравнение с рабочим профилем
sboxmgr profile diff profile.json working-profile.json
```

## Следующие шаги

1. **Phase 1**: Интеграция с Agent Bridge & Event System
2. **Phase 5**: Улучшения UI/UX
3. **Phase 6**: Продвинутые функции

---

**См. также:**
- [ADR-0017: Full Profile Architecture](../arch/decisions/ADR-0017-full-profile-architecture.md)
- [ADR-0018: Subscription Management Architecture](../arch/decisions/ADR-0018-subscription-management-architecture.md)
- [CLI Reference](../cli_reference.md) 