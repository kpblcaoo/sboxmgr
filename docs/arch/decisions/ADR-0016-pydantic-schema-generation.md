# ADR-0016: Pydantic as Single Source of Truth for Validation and Schema Generation

## Статус

**Дата:** 2025-01-27  
**Статус:** ✅ **ПРИНЯТО**  
**Контекст:** Стандартизация подхода к валидации и генерации схем

## TL;DR

- **Все валидаторы — на Pydantic BaseModel**
- **Все схемы — генерируются автоматически из этих моделей**
- **Единый источник истины:** модель → валидирует + порождает схему
- **Совместимость:** схемы используются в Go, CI, документации
- **Автоматизация:** генерация схем = часть пайплайна

## Контекст

Нужно стандартизировать подход к валидации данных и генерации схем для обеспечения совместимости между Python (sboxmgr), Go (sboxagent) и другими компонентами системы.

## Решение

### 1. Принцип единого источника истины

> **«Все валидаторы — на Pydantic. Все схемы — генерируются автоматически из этих моделей.»**

#### Преимущества:
- 🧼 **Единый источник истины** — модель → и валидирует, и порождает схему
- 🛠 **Простота поддержки** — меняешь поле → схема и валидация меняются вместе
- 🔁 **Генерация без ручной работы** — генерация `.schema.json` = одна строка
- 🧩 **Совместимость с Go и другими языками** — схема → генерит типы и валидацию
- 🧪 **Тестируемость** — легко тестировать `.schema()` и саму валидацию
- 📚 **Автоген документации** — можно делать автоматическую доку по схемам
- 📦 **Для CI/CD** — генерация схем = часть пайплайна, нет ручных рассинхронов

### 2. Архитектура по проектам

| Проект | Где валидаторы | Тип | Генерация схем |
|--------|----------------|-----|----------------|
| **sboxmgr** | `pydantic.BaseModel` | ✅ автоматическая | Да (`.schema()`) |
| **sboxagent** | Go structs + JSON | ❌ ручная/генерируемая | Из `sbox-common` |
| **sbox-common** | JSON Schemas | 🌀 из `sboxmgr` | Хранит схемы |

### 3. Модели в sboxmgr (Python CLI, генератор конфигов)

#### Уже есть или должны быть:

| Название модели | Где | Назначение |
|-----------------|-----|------------|
| `AppConfig` | ✅ | Конфигурация CLI/экспортера |
| `ParsedServer` | ✅ | Внутреннее представление сервера |
| `ExclusionList`, `ExclusionRule` | ✅ | Исключения серверов |
| `SubscriptionSource` | ✅ | Источник подписки |
| `ExportedConfig` | ✅ | Финальный экспортируемый JSON |
| `CLIArgsModel` (возможно) | 🔄 | Аргументы команд (если pydantic CLI) |
| `PostProcessorConfig` | ✅ | Конфиги постпроцессоров |
| `TagFilterSettings`, `GeoFilterSettings` | ✅ | Middleware конфиги |
| `RawSubscriptionData` | 🔄 | До обработки |

#### Требования к моделям:
- быть `BaseModel`
- иметь `.schema()` генерацию
- использовать строгую типизацию
- быть протестированы на edge-cases

### 4. Схемы в sbox-common (Shared data, схемы, протоколы)

#### Должны быть:

| Название схемы | Источник | Генератор |
|----------------|----------|-----------|
| `agent-config.schema.json` | `AgentConfigModel` | из `pydantic` |
| `integration-config.schema.json` | `IntegrationConfigModel` | из `pydantic` |
| `sboxmgr-config.schema.json` | `AppConfig` | из `pydantic` |
| `exported-config.schema.json` | `ExportedConfig` | из `pydantic` |
| `event-subscription.schema.json` | `SubscriptionEventModel` | из `pydantic` |
| `exclusion.schema.json` | `ExclusionList` | из `pydantic` |

### 5. Валидация в sboxagent (Go, оркестратор/логгер/мониторинг)

#### Должны быть:

| Что валидируется | Где используется | Как валидируется |
|------------------|------------------|------------------|
| `agent.yaml` (настройки агента) | startup/config | через JSON Schema |
| `integration.yaml` (связка) | интеграция | через JSON Schema |
| `sboxmgr.yaml` | forward в `sboxmgr` | через схему |
| Event-модели | event handling | через JSON Schema |

#### Go не умеет Pydantic, но:
- можно использовать `gojsonschema` или `cue`
- схемы всегда идут из `sbox-common/schemas/`

### 6. Структура sbox-common

#### 📁 `schemas/`
- **Автогенерируемые JSON-схемы** из `pydantic` моделей `sboxmgr`
- Используются в:
  - `sboxmgr` — для валидации CLI конфигов
  - `sboxagent` — для валидации на Go стороне

#### 📁 `protocols/`
- **Стандартизированные описания событий, API, форматов**
- Формат — JSON/YAML/OpenAPI/Markdown
- Используется обеими сторонами

#### 📁 `scripts/` (опционально)
- **Вспомогательный скрипт генерации схем**
- НЕ импортируется никем
- Исполняется вручную или по GitHub Actions

### 7. Генератор схем

```python
# scripts/generate_schemas.py
from sboxmgr.config.models import AppConfig
from sboxmgr.subscription.models import ExportedConfig, ExclusionList
# ... импорт всех моделей

def generate_schemas():
    """Generate JSON schemas from Pydantic models."""
    schemas = {
        "sboxmgr-config": AppConfig.schema(),
        "exported-config": ExportedConfig.schema(),
        "exclusion": ExclusionList.schema(),
        # ... все модели
    }
    
    for name, schema in schemas.items():
        output_path = f"sbox-common/schemas/{name}.schema.json"
        with open(output_path, 'w') as f:
            json.dump(schema, f, indent=2)
```

### 8. CI/CD интеграция

```yaml
# .github/workflows/schemas.yml
- name: Generate schemas
  run: python scripts/generate_schemas.py

- name: Check schema changes
  run: |
    if [ -n "$(git status --porcelain)" ]; then
      echo "Schema files changed - please commit them"
      exit 1
    fi
```

## Последствия

### Положительные:
- ✅ Единый источник истины для валидации и схем
- ✅ Автоматическая синхронизация без ручной работы
- ✅ Совместимость с любыми языками через JSON Schema
- ✅ Легко поддерживать, расширять, тестировать
- ✅ Отлично ложится в CI/CD и автогенерацию документации

### Отрицательные:
- ❌ Зависимость от Pydantic в Python части
- ❌ Нужен генератор схем и его поддержка
- ❌ Сложность для Go части (нужно парсить JSON Schema)

### Риски:
- 🔴 Рассинхронизация схем и кода при ошибках в генераторе
- 🔴 Сложность отладки валидации в Go
- ⚠️ Нужна четкая документация процесса генерации

## Альтернативы

### A. Ручное написание схем
- ❌ Дублирование логики
- ❌ Рассинхронизация
- ❌ Сложность поддержки

### B. Генерация из Go структур
- ❌ Go не имеет такой мощной системы валидации
- ❌ Сложность обратной совместимости

### C. Использование OpenAPI/Swagger
- ❌ Избыточность для внутренних схем
- ❌ Сложность для простых случаев

## Реализация

### Phase 1: Foundation
- [ ] Создать `scripts/generate_schemas.py`
- [ ] Добавить `.schema()` ко всем существующим моделям
- [ ] Создать `sbox-common/schemas/` структуру
- [ ] Настроить CI проверку генерации схем

### Phase 2: Integration
- [ ] Интегрировать схемы в `sboxagent` (Go)
- [ ] Добавить валидацию по схемам в CLI
- [ ] Создать документацию по схемам

### Phase 3: Advanced Features
- [ ] Автогенерация документации из схем
- [ ] Валидация CLI-аргументов через pydantic
- [ ] Typed-config инициализация

## Связанные ADR

- ADR-0007: Validator Architecture and Pipeline Context
- ADR-0009: Configuration System Architecture
- ADR-0015: Agent-Installer Separation & Installation Strategy 