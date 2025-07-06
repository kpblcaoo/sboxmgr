# План рефакторинга: profiles → configs + TOML

**Дата:** 2024-12-19
**Ветка:** feature/profile-to-config-migration
**Цель:** Переименование profiles в configs с добавлением TOML поддержки

## 🎯 **ЦЕЛЬ РЕФАКТОРИНГА**

Устранить путаницу в терминологии "профили" и улучшить пользовательский опыт:
- **profiles** → **configs** (пользовательские конфигурации)
- **Добавить TOML поддержку** для лучшего UX
- **Оставить JSON только для ClientConfig** (внутренний экспорт)
- **Структурировать хранилище** configs/*.toml

## 📋 **ПЛАН ВЫПОЛНЕНИЯ**

### Этап 1: Переименование классов и моделей
- [ ] `FullProfile` → `UserConfig`
- [ ] `SubscriptionProfile` → `SubscriptionConfig`
- [ ] `FilterProfile` → `FilterConfig`
- [ ] `RoutingProfile` → `RoutingConfig`
- [ ] `ExportProfile` → `ExportConfig`
- [ ] `AgentProfile` → `AgentConfig`
- [ ] `UIProfile` → `UIConfig`
- [ ] `ClientProfile` → `ClientConfig` (остается JSON)
- [ ] `InboundProfile` → `InboundConfig` (остается JSON)

### Этап 2: Переименование модулей и пакетов
- [ ] `src/sboxmgr/profiles/` → `src/sboxmgr/configs/`
- [ ] `src/sboxmgr/profiles/models.py` → `src/sboxmgr/configs/models.py`
- [ ] `src/sboxmgr/profiles/loader.py` → `src/sboxmgr/configs/loader.py`
- [ ] `src/sboxmgr/profiles/manager.py` → `src/sboxmgr/configs/manager.py`
- [ ] `src/sboxmgr/profiles/cli.py` → `src/sboxmgr/configs/cli.py`

### Этап 3: Добавление TOML поддержки
- [ ] Расширить ConfigLoader для поддержки TOML
- [ ] Добавить зависимость toml в pyproject.toml
- [ ] Создать TOML сериализацию/десериализацию
- [ ] Добавить валидацию TOML файлов

### Этап 4: Обновление CLI команд
- [ ] `sboxctl profile` → `sboxctl config`
- [ ] `sboxctl config list` - показать все конфигурации
- [ ] `sboxctl config apply home.toml` - применить конфигурацию
- [ ] `sboxctl config switch work` - переключить конфигурацию
- [ ] `sboxctl config edit home` - редактировать конфигурацию
- [ ] `sboxctl config create` - создать новую конфигурацию

### Этап 5: Изменение структуры хранилища
- [ ] `~/.config/sboxmgr/profiles/` → `~/.config/sboxmgr/configs/`
- [ ] Поддержка формата: `configs/{name}.toml`
- [ ] Создать default.toml как базовую конфигурацию
- [ ] Миграция существующих JSON профилей в TOML

### Этап 6: Обновление документации
- [ ] Обновить все ссылки profile → config
- [ ] Создать примеры TOML конфигураций
- [ ] Обновить CLI справку
- [ ] Создать миграционное руководство

### Этап 7: Тестирование
- [ ] Обновить все тесты с новой терминологией
- [ ] Тесты TOML загрузки/сохранения
- [ ] Тесты миграции JSON → TOML
- [ ] Интеграционные тесты CLI команд

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
