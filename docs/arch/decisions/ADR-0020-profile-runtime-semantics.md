# ADR-0020: Profile Runtime Semantics & Outbound Management

## Статус

**Дата:** 2025-07-01  
**Статус:** 🔄 **В РАЗРАБОТКЕ**  
**Контекст:** Runtime семантика профилей, управление outbounds и маршрутизацией

## TL;DR

- **Outbounds НЕ хранятся в профиле** - только OutboundPolicy для генерации
- **Маршрутизация из подписок** - через RoutingPolicyBuilder с дефолтами
- **Кеширование по хешам** - для оптимизации pipeline
- **Версионирование** - в meta секции профиля
- **Геофильтрация** - предупреждения, не исключения по умолчанию

## Контекст

Нужно определить, как профили взаимодействуют с динамическими данными (подписки, outbounds, маршрутизация) и как обеспечить эффективность и безопасность.

## Решение

### 1. Outbound Management

#### Outbounds НЕ в профиле
```python
# ❌ НЕ делаем так
class FullProfile(BaseModel):
    outbounds: List[OutboundConfig]  # НЕТ!

# ✅ Делаем так  
class FullProfile(BaseModel):
    outbound_policy: OutboundPolicy
    routing_policy: RoutingPolicy
```

#### OutboundPolicy для генерации
```python
class OutboundPolicy(BaseModel):
    group_by: Literal["subscription", "country", "custom"] = "subscription"
    strategy: Literal["url_test", "random", "fallback", "geo"] = "url_test"
    include_tags: List[str] = []
    exclude_tags: List[str] = []
    max_per_group: int = 5
    deduplicate: bool = True
```

### 2. Routing from Subscriptions

#### Принцип: доверяй, но проверяй
```python
class RoutingPolicy(BaseModel):
    mode: Literal["manual", "auto"] = "auto"
    default_group: str = "auto"
    ruleset_strategy: Literal["geoip", "domain_suffix", "subscription_tags"] = "geoip"
    fallback_to_proxy: bool = True
    trust_subscription_rules: bool = False  # Безопасность по умолчанию
```

#### Pipeline обработки
```
[Подписки] → [Парсинг → ParsedServer[]]
                    |
               [Exclusions] → ❌ Удалить
                    |
          [PostProcessorChain] → 💡 Geo/Latency/Dedup
                    |
            [OutboundPolicyBuilder]
                    |
           [RoutingPolicyBuilder] → Rules
                    |
            [FinalConfigExporter]
```

### 3. Caching & Change Detection

#### Хеширование на разных уровнях
```python
class ProfileMetadata(BaseModel):
    generated_by: str = "sboxmgr"
    sboxmgr_version: str
    profile_schema_version: str = "1.0.0"
    timestamp: datetime
    cache_hashes: Dict[str, str] = {}  # source_url -> hash
```

#### Кеш-хеши
- `raw_hash` - хеш сырой подписки
- `parsed_hash` - хеш ParsedServer[]
- `outbounds_hash` - хеш сгенерированных outbounds
- `routing_hash` - хеш routing rules

### 4. Geo Filtering Policy

#### Безопасный подход
```python
class GeoFilterPolicy(BaseModel):
    exclude_geo: List[str] = []  # Пусто по умолчанию
    warn_geo: List[str] = ["CN"]  # Предупреждения
    warn_message: str = "⚠️ Server in {country}. May be fake/trap."
```

#### UX принципы
- ❌ НЕ исключать CN по умолчанию
- ✅ Показывать предупреждения
- ✅ Давать опцию `--exclude-geo CN`
- ✅ Объяснять в документации

### 5. Versioning Strategy

#### Meta секция в профиле
```json
{
  "meta": {
    "generated_by": "sboxmgr",
    "sboxmgr_version": "1.5.0",
    "profile_schema_version": "1.0.0",
    "timestamp": "2025-07-01T12:00:00Z",
    "cache_hashes": {
      "https://sub.example.com": "sha256:abc123..."
    }
  }
}
```

#### Версионирование компонентов
| Компонент | Где версия | Пример |
|-----------|------------|--------|
| sboxmgr | meta.sboxmgr_version | 1.5.0 |
| Profile Schema | meta.profile_schema_version | 1.0.0 |
| sing-box | meta.singbox_version | 1.8.9 |
| Plugins | plugins/*/manifest.json | 1.0.0 |

## Последствия

### Положительные:
- ✅ **Безопасность** - не доверяем маршрутам из подписок
- ✅ **Производительность** - кеширование по хешам
- ✅ **Гибкость** - политики вместо хардкода
- ✅ **Версионирование** - полная трассируемость
- ✅ **UX** - предупреждения вместо блокировки

### Отрицательные:
- ❌ **Сложность** - больше компонентов
- ❌ **Производительность** - вычисление хешей
- ❌ **Размер** - meta секция увеличивает профили

### Риски:
- 🔴 **Кеш-инвалидация** - неправильные хеши
- 🔴 **Безопасность** - ложные предупреждения
- ⚠️ **UX** - слишком много предупреждений

## Альтернативы

### A. Хранить outbounds в профиле
- ❌ Размер профилей
- ❌ Рассинхронизация с подписками
- ❌ Сложность обновления

### B. Доверять маршрутам из подписок
- ❌ Безопасность
- ❌ Контроль над routing

### C. Исключать CN по умолчанию
- ❌ UX (может обидеть пользователей)
- ❌ Потеря валидных серверов

## Реализация

### Phase 1: Foundation
- [ ] Создать OutboundPolicy и RoutingPolicy модели
- [ ] Реализовать ProfileMetadata с версионированием
- [ ] Добавить кеш-хеши в pipeline

### Phase 2: Integration
- [ ] Интегрировать с существующими компонентами
- [ ] Добавить GeoFilterPolicy
- [ ] Реализовать предупреждения в CLI

### Phase 3: Advanced
- [ ] Оптимизация кеширования
- [ ] GUI поддержка предупреждений
- [ ] SaaS интеграция

## Связанные ADR

- ADR-0017: Full Profile Architecture
- ADR-0019: Full Profile UX & Runtime Management
- ADR-0016: Pydantic Schema Generation
- ADR-0008: Defaults and Fail-Tolerance 