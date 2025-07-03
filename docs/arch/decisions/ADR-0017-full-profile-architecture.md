# ADR-0017: Full Profile Architecture

## Статус

**Дата:** 2025-06-29  
**Статус:** ✅ **ПРИНЯТО**  
**Контекст:** Единая конфигурационная сущность для всего пайплайна

## TL;DR

- **Full Profile** = единая конфигурационная сущность, охватывающая все настраиваемые компоненты
- **profile.json** содержит: подписки, маршруты, фильтры, экспорт, настройки агента, UI
- **CLI команды:** `sboxmgr apply --profile profiles/home.json`
- **SaaS-ready:** профили легко сериализуются в БД/облако
- **Решает конфликт UI/CLI:** профиль как единый источник истины

## Контекст

Текущая архитектура имеет разрозненные конфигурационные файлы:
- `config.json` - настройки CLI
- `exclusions.json` - исключения серверов  
- `subscriptions.yaml` - источники подписок
- Различные CLI флаги для маршрутизации и экспорта

Это создает проблемы:
- Сложность управления множественными файлами
- Конфликты между UI и CLI настройками
- Сложность для SaaS (множественные сущности в БД)
- Отсутствие единой точки конфигурации

## Решение

### 1. Full Profile как единая сущность

```json
{
  "id": "home",
  "description": "Домашний профиль с Pi-hole, VPN и минимальным обходом",
  "subscriptions": [
    "https://sub.example.com/vless",
    "local/ss.json"
  ],
  "filters": {
    "exclude_tags": ["ads", "test"],
    "only_tags": ["trusted"],
    "exclusions": ["server1", "server2"]
  },
  "routing": {
    "proxy1.example.com": "tunnel",
    "proxy2.example.com": "direct",
    "default_route": "tunnel"
  },
  "export": {
    "format": "sing-box",
    "outbound_profile": "vless-real",
    "inbound_profile": "tun",
    "output_file": "config.json"
  },
  "middleware": ["TagFilter", "EnrichGeo", "RouteByLatency"],
  "agent": {
    "auto_restart": false,
    "monitor_latency": true,
    "health_check_interval": "30s"
  },
  "ui": {
    "default_language": "ru",
    "mode": "tui"
  }
}
```

### 2. CLI команды

```bash
# Применение профиля
sboxmgr apply --profile profiles/home.json

# Валидация профиля
sboxmgr validate-profile profiles/home.json

# Объяснение профиля
sboxmgr explain --profile profiles/home.json

# Сравнение профилей
sboxmgr diff --profile home --profile work

# Экспорт части профиля
sboxmgr export --part routing
sboxmgr export --part subscriptions
```

### 3. Интеграция с существующими компонентами

#### Обратная совместимость
- Существующие файлы (`exclusions.json`, `config.json`) продолжают работать
- CLI флаги имеют приоритет над профилем
- Постепенная миграция через `--profile` флаг

#### Миграционный путь
```bash
# Старый способ (продолжает работать)
sboxmgr export -u https://sub.example.com

# Новый способ
sboxmgr apply --profile profiles/home.json

# Гибридный способ
sboxmgr apply --profile profiles/home.json --override-subscription https://new-sub.example.com
```

### 4. SaaS интеграция

#### Модель в БД
```json
{
  "user_id": "u_123",
  "profile_id": "home-vpn",
  "active": true,
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T15:30:00Z",
  "data": { ... } // embedded full profile
}
```

#### API endpoints
- `GET /api/users/{user_id}/profiles` - список профилей
- `POST /api/users/{user_id}/profiles` - создание профиля
- `PUT /api/users/{user_id}/profiles/{profile_id}` - обновление
- `POST /api/users/{user_id}/profiles/{profile_id}/apply` - применение

## Последствия

### Положительные:
- ✅ **Централизация** - один JSON → все настройки
- ✅ **Простое переключение** - `sboxmgr apply --profile home.json`
- ✅ **A/B тестирование** - профили: home, work, vpn-only, ci-test
- ✅ **Удобство для UI** - один YAML/JSON формирует всю панель
- ✅ **SaaS-ready** - профили легко сериализуются в БД/облако
- ✅ **Решает конфликт UI/CLI** - профиль как единый источник истины
- ✅ **Версионирование** - профили можно хранить в Git

### Отрицательные:
- ❌ **Сложность миграции** - нужно перевести существующие конфиги
- ❌ **Размер файлов** - профили могут быть большими
- ❌ **Валидация** - сложность валидации вложенных структур
- ❌ **Производительность** - загрузка больших профилей

### Риски:
- 🔴 **Рассинхронизация** - профиль vs отдельные файлы
- 🔴 **Сложность отладки** - где именно проблема в большом профиле
- ⚠️ **Обратная совместимость** - нужно поддерживать старые способы

## Альтернативы

### A. Оставить текущую архитектуру
- ❌ Сложность для SaaS
- ❌ Конфликты UI/CLI
- ❌ Множественные файлы

### B. Только для SaaS
- ❌ Дублирование логики
- ❌ Разные подходы для CLI и SaaS

### C. Микро-профили
- ❌ Сложность композиции
- ❌ Потеря централизации

## Реализация

### Phase 1: Foundation
- [ ] Создать Pydantic модели для Profile
- [ ] Создать schema для profile.json
- [ ] Базовые CLI команды: apply, validate, explain
- [ ] Обратная совместимость с существующими файлами

### Phase 2: Integration
- [ ] Интеграция с существующими компонентами
- [ ] Миграционные утилиты
- [ ] Тесты для всех сценариев
- [ ] Документация и примеры

### Phase 3: Advanced Features
- [ ] Diff между профилями
- [ ] Экспорт частей профиля
- [ ] Шаблоны профилей
- [ ] SaaS интеграция

## Связанные ADR

- ADR-0003: Subscription Models & Normalization
- ADR-0005: Extensible Routing Layer
- ADR-0009: Configuration System Architecture
- ADR-0015: Agent-Installer Separation & Installation Strategy
- ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation 