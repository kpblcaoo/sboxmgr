# План рефакторинга: profiles → configs + TOML

**Дата:** 2025-07-06
**Ветка:** feature/profile-to-config-migration
**Цель:** Переименование profiles в configs с добавлением TOML поддержки

## 🎯 **ЦЕЛЬ РЕФАКТОРИНГА**

Устранить путаницу в терминологии "профили" и улучшить пользовательский опыт:
- **profiles** → **configs** (пользовательские конфигурации)
- **Добавить TOML поддержку** для лучшего UX
- **Оставить JSON только для ClientConfig** (внутренний экспорт)
- **Структурировать хранилище** configs/*.toml

## 📋 **ПЛАН ВЫПОЛНЕНИЯ**

### Этап 1: Переименование классов и моделей ✅
- [x] `FullProfile` → `UserConfig`
- [x] `SubscriptionProfile` → `SubscriptionConfig`
- [x] `FilterProfile` → `FilterConfig`
- [x] `RoutingProfile` → `RoutingConfig`
- [x] `ExportProfile` → `ExportConfig`
- [x] `AgentProfile` → `AgentConfig`
- [x] `UIProfile` → `UIConfig`
- [x] `ClientProfile` → `ClientConfig` (остается JSON)
- [x] `InboundProfile` → `InboundConfig` (остается JSON)

### Этап 2: Переименование модулей и пакетов ✅
- [x] `src/sboxmgr/profiles/` → `src/sboxmgr/configs/`
- [x] `src/sboxmgr/profiles/models.py` → `src/sboxmgr/configs/models.py`
- [x] `src/sboxmgr/profiles/loader.py` → `src/sboxmgr/configs/loader.py`
- [x] `src/sboxmgr/profiles/manager.py` → `src/sboxmgr/configs/manager.py`
- [x] `src/sboxmgr/profiles/cli.py` → `src/sboxmgr/configs/cli.py`

### Этап 3: Добавление TOML поддержки ✅
- [x] Расширить ConfigLoader для поддержки TOML
- [x] Добавить зависимость toml в pyproject.toml
- [x] Создать TOML сериализацию/десериализацию
- [x] Добавить валидацию TOML файлов

### Этап 4: Обновление документации ✅
- [x] Обновить все ссылки profile → config
- [x] Переименовать `docs/user-guide/profiles.md` → `docs/user-guide/configs.md`
- [x] Обновить CLI reference с новыми командами
- [x] Обновить README с новыми ссылками
- [x] Обновить схемы в `schemas/README.md`
- [x] Создать примеры TOML конфигураций
- [x] Обновить ссылки в `docs/user-guide/subscriptions.md`

### Этап 5: Тестирование ✅
- [x] Обновить все тесты с новой терминологией
- [x] Тесты TOML загрузки/сохранения
- [x] Тесты enum-сериализации (обе стороны)
- [x] Тесты валидации при switch (TOML синтаксис + UserConfig.validate())
- [x] Тесты CLI fallback (--config и SBOXMGR_ACTIVE_CONFIG)
- [x] Тесты edge cases: no configs, corrupted .active_config, invalid enum
- [x] Комплексные тесты CLI команд: list, switch, status, validate
- [x] Создан test_config_management.py с 17 тестами

## 🗂️ **СТРУКТУРА ПОСЛЕ РЕФАКТОРИНГА**

### Пользовательские конфигурации (TOML):
```
~/.config/sboxmgr/configs/
├── default.toml         # Базовая конфигурация
├── home.toml           # Домашняя конфигурация
├── work.toml           # Рабочая конфигурация
└── travel.toml         # Конфигурация для путешествий
```

### Код структура:
```
src/sboxmgr/configs/
├── __init__.py
├── models.py           # UserConfig, SubscriptionConfig, etc.
├── loader.py           # ConfigLoader с TOML поддержкой
├── manager.py          # ConfigManager
├── cli.py             # CLI команды
└── migrator.py        # Миграция JSON → TOML
```

## 📝 **ПРИМЕР TOML КОНФИГУРАЦИИ**

```toml
# ~/.config/sboxmgr/configs/home.toml
id = "home"
description = "Домашняя конфигурация"
version = "1.0"

[subscriptions]
# Подписки
[[subscriptions.sources]]
id = "main"
url = "https://my-provider.com/subscription"
enabled = true
priority = 1

[filters]
# Фильтры
exclude_tags = ["blocked", "slow"]
only_tags = ["premium"]
exclusions = ["bad-server.com"]

[routing]
# Маршрутизация
default_route = "tunnel"
[routing.custom_routes]
"youtube.com" = "direct"
"github.com" = "direct"

[export]
# Экспорт
format = "sing-box"
inbound_types = ["socks", "http"]
socks_port = 1080
http_port = 8080
output_file = "home-config.json"

[agent]
# Агент
auto_restart = true
monitor_latency = true
health_check_interval = "30s"
log_level = "info"

[ui]
# Интерфейс
default_language = "ru"
mode = "cli"
show_debug_info = false
```

## 🔄 **МИГРАЦИЯ**

### Автоматическая миграция:
```bash
# Миграция всех JSON профилей в TOML
sboxctl config migrate --from ~/.config/sboxmgr/profiles/ --to ~/.config/sboxmgr/configs/

# Миграция конкретного профиля
sboxctl config migrate --profile home.json --output home.toml
```

### Обратная совместимость:
- JSON профили будут поддерживаться в режиме только чтения
- Предупреждения о deprecated JSON формате
- Автоматическое предложение миграции

## 🚀 **ПРЕИМУЩЕСТВА ПОСЛЕ РЕФАКТОРИНГА**

1. **Ясная терминология**: config вместо profile
2. **Лучший UX**: TOML читаемее JSON
3. **Комментарии**: TOML поддерживает комментарии
4. **Структурированность**: configs/*.toml в одном месте
5. **CLI дружелюбность**: простые команды config
6. **Расширяемость**: легко добавлять новые секции

## 📊 **ОЦЕНКА ТРУДОЗАТРАТ**

- **Этап 1-2**: Переименование (2-3 дня)
- **Этап 3**: TOML поддержка (1-2 дня)
- **Этап 4**: CLI команды (1-2 дня)
- **Этап 5**: Структура хранилища (1 день)
- **Этап 6**: Документация (1 день)
- **Этап 7**: Тестирование (2-3 дня)

**Итого: 8-12 дней** полноценной работы

## ⚠️ **РИСКИ И МИГРАЦИЯ**

- **Обратная совместимость**: Поддержка JSON профилей
- **Пользовательские данные**: Не потерять существующие профили
- **Тестирование**: Полное покрытие тестами
- **Документация**: Обновить все ссылки

## 🎭 **СОВМЕСТИМОСТЬ**

### Поддерживаемые форматы:
- **TOML**: Основной формат для пользователей
- **JSON**: Только для ClientConfig (внутренний)
- **YAML**: Возможно в будущем

### Команды совместимости:
```bash
# Новые команды (основные)
sboxctl config list
sboxctl config apply home.toml
sboxctl config switch work

# Старые команды (deprecated, но работают)
sboxctl profile list  # → warning + redirect
sboxctl profile apply home.json  # → warning + migrate
```

## 🏁 **КРИТЕРИИ ГОТОВНОСТИ**

✅ **Готово когда:**
- [ ] Все тесты проходят
- [ ] CLI команды работают
- [ ] Документация обновлена
- [ ] Миграция JSON → TOML работает
- [ ] Пользовательские данные сохранены
- [ ] Обратная совместимость обеспечена

---

**Статус:** 🔄 **В ПЛАНАХ**
**Приоритет:** 🔥 **Высокий** (после завершения code-quality-analysis)
**Ответственный:** AI Assistant
**Дата начала:** После завершения текущей ветки качества кода
