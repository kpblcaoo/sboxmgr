# ADR-0018: Subscription Management Architecture

## Статус

**Дата:** 2025-06-29  
**Статус:** ✅ **ПРИНЯТО**  
**Контекст:** Расширенное управление подписками с профилями, изоляцией и автоматическим переключением

## TL;DR

- **SubscriptionSource** = базовая единица подписки с метаданными (id, enabled, tags, priority)
- **Profile-driven** = подписки управляются через профили (ADR-0017)
- **Isolation** = возможность использовать подписки раздельно или объединять
- **Auto-switching** = автоматическое переключение по политикам (latency, availability, geo)
- **CLI UX** = `sboxmgr subscription add/remove/enable/disable/preview`

## Контекст

Текущая реализация имеет ограничения:
- Все подписки всегда объединяются в общий пул
- Нет возможности временно отключить подписку
- Отсутствует изоляция подписок для разных use-cases
- Нет автоматического переключения при проблемах
- Сложность управления множественными подписками

## Решение

### 1. Расширенная модель SubscriptionSource

```yaml
# subscription_sources.yaml
subscriptions:
  - id: "china_vless"
    url: "https://sub.example.com/china"
    type: "vless"
    enabled: true
    priority: 1
    tags: ["china", "streaming"]
    description: "Китайские серверы для стриминга"
    
  - id: "work_ss"
    url: "https://sub.example.com/work"
    type: "shadowsocks"
    enabled: false  # временно отключена
    priority: 2
    tags: ["work", "stable"]
    description: "Рабочие серверы"
    
  - id: "backup_clash"
    url: "https://sub.example.com/backup"
    type: "clash"
    enabled: true
    priority: 3
    tags: ["backup", "fallback"]
    description: "Резервные серверы"
```

### 2. Интеграция с Full Profile (ADR-0017)

```json
{
  "id": "home",
  "subscriptions": [
    {
      "id": "china_vless",
      "enabled": true,
      "priority": 1
    },
    {
      "id": "work_ss", 
      "enabled": false,
      "priority": 2
    }
  ],
  "filters": {
    "exclude_tags": ["test"],
    "only_enabled": true
  },
  "routing": {
    "by_source": {
      "china_vless": "tunnel",
      "work_ss": "direct"
    }
  }
}
```

### 3. CLI команды управления

```bash
# Базовое управление
sboxmgr subscription add https://sub.example.com --id china --type vless --tags china,streaming
sboxmgr subscription remove china
sboxmgr subscription enable china
sboxmgr subscription disable china

# Просмотр и инспекция
sboxmgr subscription list --status
sboxmgr subscription preview china --format json
sboxmgr subscription show china --servers

# Изоляция и фильтрация
sboxmgr export --only-source china
sboxmgr export --exclude-source work
sboxmgr export --route-by-source

# Профили (интеграция с ADR-0017)
sboxmgr profile apply home --subscriptions china,work
sboxmgr profile switch work
```

### 4. Автоматическое переключение

#### Policy Engine
```yaml
# subscription_policies.yaml
policies:
  - name: "latency_fallback"
    condition:
      - source: "china_vless"
        max_latency: 300
        switch_to: "backup_clash"
    
  - name: "geo_switch"
    condition:
      - when: "user_location == 'CN'"
        enable: ["china_vless"]
        disable: ["work_ss"]
    
  - name: "availability_check"
    condition:
      - source: "work_ss"
        health_check: true
        failure_threshold: 3
        switch_to: "backup_clash"
```

#### Runtime Monitoring
```python
class SubscriptionMonitor:
    def check_health(self, source_id: str) -> HealthStatus
    def measure_latency(self, source_id: str) -> float
    def get_user_location(self) -> str
    
class PolicyEngine:
    def evaluate_policies(self, context: RuntimeContext) -> List[Action]
    def apply_actions(self, actions: List[Action]) -> None
```

### 5. Изоляция подписок

#### Режимы работы
1. **Unified Mode** (по умолчанию) - все enabled подписки объединяются
2. **Isolated Mode** - каждая подписка обрабатывается отдельно
3. **Grouped Mode** - подписки группируются по тегам или профилям

#### CLI флаги
```bash
# Режимы
sboxmgr export --mode unified    # все подписки в один конфиг
sboxmgr export --mode isolated   # отдельный конфиг для каждой подписки
sboxmgr export --mode grouped    # группировка по тегам

# Фильтрация
sboxmgr export --only-tags china,streaming
sboxmgr export --exclude-tags test,backup
sboxmgr export --priority 1,2
```

## Интеграция с существующими ADR

### ✅ ADR-0003: Subscription Models
- **Совместимо**: SubscriptionSource остается базовой единицей
- **Расширение**: добавлены поля enabled, priority, tags, description
- **Обратная совместимость**: старые подписки работают без изменений

### ✅ ADR-0017: Full Profile Architecture  
- **Интеграция**: подписки управляются через профили
- **Единый источник**: profile.json содержит настройки подписок
- **CLI**: `sboxmgr apply --profile` применяет настройки подписок

### ✅ ADR-0016: Pydantic Schema Generation
- **Валидация**: SubscriptionSourceModel с автоматической генерацией схем
- **CLI**: `sboxmgr validate-subscription` использует Pydantic валидацию
- **API**: схемы для subscription_sources.yaml и subscription_policies.yaml

### ✅ ADR-0015: Agent-Installer Separation
- **Агент**: может переключать профили и подписки через integration.yaml
- **Мониторинг**: агент собирает метрики для PolicyEngine
- **Автоматизация**: агент применяет политики переключения

### ✅ ADR-0012: Service Architecture
- **Трехуровневая архитектура**: CLI → Agent → Installer
- **Dual-path**: CLI и агент используют одинаковые модели подписок
- **События**: SubscriptionManager отправляет события о изменениях

## Последствия

### Положительные:
- ✅ **Гибкость**: изоляция, группировка, автоматическое переключение
- ✅ **UX**: простые CLI команды для управления подписками
- ✅ **Надежность**: автоматическое переключение при проблемах
- ✅ **Масштабируемость**: поддержка множественных подписок
- ✅ **Интеграция**: полная совместимость с профилями (ADR-0017)
- ✅ **Обратная совместимость**: существующие конфиги продолжают работать

### Отрицательные:
- ❌ **Сложность**: больше конфигурационных файлов
- ❌ **Производительность**: мониторинг и политики требуют ресурсов
- ❌ **Отладка**: сложнее понять, какая подписка используется
- ❌ **Конфликты**: возможны конфликты между политиками

### Риски:
- 🔴 **Состояние**: сложность синхронизации состояния между CLI и агентом
- 🔴 **Производительность**: мониторинг множественных подписок
- ⚠️ **UX**: пользователи могут запутаться в режимах работы

## Реализация

### Phase 1: Foundation
- [ ] Расширить SubscriptionSourceModel (enabled, priority, tags, description)
- [ ] Обновить SubscriptionManager для поддержки enabled/disabled
- [ ] CLI команды: add, remove, enable, disable, list
- [ ] Обратная совместимость с существующими подписками

### Phase 2: Isolation & Filtering
- [ ] Режимы работы: unified, isolated, grouped
- [ ] CLI флаги: --only-source, --exclude-source, --only-tags
- [ ] Интеграция с профилями (ADR-0017)
- [ ] Тесты для всех режимов работы

### Phase 3: Auto-switching
- [ ] PolicyEngine для автоматического переключения
- [ ] SubscriptionMonitor для сбора метрик
- [ ] Runtime политики: latency, availability, geo
- [ ] Интеграция с агентом (ADR-0015)

### Phase 4: Advanced Features
- [ ] TUI для управления подписками
- [ ] Hot reload конфигурации
- [ ] Метрики и мониторинг
- [ ] ML/Heuristic routing

## Связанные ADR

- ADR-0003: Subscription Models & Normalization
- ADR-0017: Full Profile Architecture
- ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation
- ADR-0015: Agent-Installer Separation & Installation Strategy
- ADR-0012: Service Architecture & Dual-Path Support 