# Other languages / Другие языки
- [Русский (docs/ru/DEVELOPMENT.md)](docs/ru/DEVELOPMENT.md)

# Onboarding

Welcome to the development process! If you are new to the project, please follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kpblcaoo/update-singbox.git
   cd update-singbox
   ```
2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Install development dependencies:**
   ```bash
   pip install .[dev]
   ```
4. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```
5. **Run tests:**
   ```bash
   pytest
   ```
6. **Read the CONTRIBUTING section in README.md for coding standards and PR process.**

---

# Процесс разработки и релиза

## Базовые ветки

| Branch | Purpose |
|--------|---------|
| `main` | Always-green, production-ready. Release tags (`v1.4.0`, `v1.5.0` …). |
| `develop` | Integration branch for the next version (currently 1.5.0). |
| `release/x.y.z` | Pre-release stabilization; hot fixes only. Merged back to `main` & `develop`. |
| `hotfix/x.y.z+1` | Critical fix for `main`; cherry-picked back to `develop`. |

### Feature branches
Create short-lived branches from `develop`:

```bash
git checkout develop && git pull
git checkout -b feat/C-01-pydantic-models
```

Merge via Pull Request → squash-merge into `develop`.

## CI / CD Workflows

| Workflow | Trigger |
|----------|---------|
| `ci.yml` | Pull Requests & pushes to `develop` / feature branches — lint, tests, coverage |
| `release.yml` | Tagged commits on `main` — build, publish artefacts, PyPI, Docker |

## Best practices для плагинной архитектуры подписочного пайплайна

### Как устроены плагины
- Все ключевые этапы пайплайна (fetcher, parser, exporter) реализованы как отдельные классы/модули.
- Регистрация плагинов происходит через декоратор `@register` или через registry.
- Каждый плагин реализует минимальный контракт (например, метод `fetch`, `parse`, `export`).

### Как добавить новый протокол
1. Реализуйте новый класс-плагин (например, `TuicExporter`, `WireguardParser`).
2. Зарегистрируйте его через `@register("имя_типа")`.
3. При необходимости расширьте модель `ParsedServer` (новые поля — всегда опциональны).
4. Добавьте тесты (unit/smoke) на новый тип.

### Fail-tolerance
- Если тип не поддержан плагином — выводится warning, сервер скипается, пайплайн не падает.
- Это позволяет внедрять новые протоколы поэтапно, не ломая рабочие сценарии.

### Тестирование плагинов
- Для каждого нового типа добавляйте unit/smoke-тест (в edge/ или tests/).
- Покрывайте edge-cases (отсутствие обязательных полей, некорректные значения).

### Рекомендации по изоляции логики
- Экспортёры, парсеры, фетчеры не зависят друг от друга напрямую.
- Логику для каждого протокола можно вынести в отдельный файл/пакет.
- В будущем возможно вынести edge-плагины в отдельные пакеты (pip install ...).
- Поддержка внешних плагинов (через entrypoints/importlib) возможна без изменений основной архитектуры.

### Почему архитектура не монолитна
- Все расширения делаются через плагины, а не через изменение ядра.
- Новые типы не требуют переписывать существующий код.
- Fail-tolerance и backward-compatibility встроены в основу пайплайна.

# Middleware: паттерн, best practices и тестирование

## Что такое middleware
- Middleware — это расширяемые обработчики, которые применяются к списку ParsedServer между парсером и постпроцессором.
- Каждый middleware реализует метод `process(servers, context)`, может фильтровать, обогащать или логировать сервера.
- MiddlewareChain позволяет выстраивать цепочку из нескольких middleware, порядок влияет на результат.

## Пример
```python
from sboxmgr.subscription.middleware_base import MiddlewareChain, TagFilterMiddleware, EnrichMiddleware
chain = MiddlewareChain([
    TagFilterMiddleware(),
    EnrichMiddleware(),
])
servers = chain.process(servers, context)
```

## Best practices
- Каждый middleware должен быть stateless (не хранить состояние между вызовами).
- Всегда проверяйте, что входные данные корректны (список ParsedServer).
- Для логирования используйте LoggingMiddleware с учётом debug_level из context.
- Для фильтрации используйте TagFilterMiddleware (по context.tag_filters).
- Для обогащения — EnrichMiddleware (пример: добавить country, latency и т.д.).
- Порядок middleware важен: сначала фильтрация, потом enrich, потом логирование.
- Ошибки в middleware должны аккумулироваться в context.metadata['errors'] (через PipelineError), а не приводить к падению пайплайна.

## Тестирование
- Покрывайте edge-cases: пустой список, пустая цепочка, несколько одинаковых middleware, ошибки внутри middleware, отсутствие нужных полей в context.
- Используйте capsys для проверки debug-вывода LoggingMiddleware.
- Проверяйте, что порядок middleware влияет на результат (см. tests/edge/test_parser_edge_cases.py).

## Расширение
- Для новых сценариев реализуйте свой middleware, зарегистрируйте его в цепочке.
- Документируйте публичные методы Google-style docstring.
- Добавляйте edge-тесты для новых middleware.

# Кеширование в SubscriptionManager и fetcher

## Как работает кеш
- Для ускорения и снижения нагрузки используется in-memory кеш (dict + threading.Lock) на время процесса.
- Кеш реализован в SubscriptionManager (get_servers) и во всех fetcher'ах (fetch).
- Ключ кеша строится из url, user_agent, headers, tag_filters, mode (для fetcher — url, user_agent, headers).
- Ошибки не кешируются, только успешные результаты.
- Для сброса кеша используйте параметр force_reload=True.

## Best practices
- Используйте кеш по умолчанию для CLI, тестов, DX.
- Для критичных сценариев (например, обновление подписки) вызывайте с force_reload=True.
- Не используйте кеш для долгосрочного хранения или между сессиями (in-memory only).
- Кеш не сохраняется между процессами, не используется на диске.
- Для режимов с повышенной безопасностью (secure_mode, debug_level > 0) кеш можно отключать вручную.

## Безопасность
- Кеш не содержит чувствительных данных на диске, работает только в памяти процесса.
- Ключ кеша учитывает все влияющие параметры, чтобы избежать подмены данных.
- Все сек-рекомендации по кешу отмечены как mitigated в security.md.

# [2025-06-22] Архитектурный прогресс и завершённые задачи

- Все критичные архитектурные задачи по middleware, edge-case тестированию, кешированию и fail-tolerance выполнены и покрыты тестами (>90% coverage).
- Middleware (BaseMiddleware, MiddlewareChain, LoggingMiddleware, TagFilterMiddleware, EnrichMiddleware) реализованы и протестированы на edge-cases.
- Кеширование реализовано в SubscriptionManager и fetcher'ах, ошибки не кешируются, force_reload поддерживается.
- Все best practices и паттерны зафиксированы в этом документе и в плане subscription_pipeline.md.
- Документированы примеры использования middleware, кеша, и рекомендации по тестированию edge-cases.

# DX: CLI-генератор шаблонов плагинов (plugin-template)

Для ускорения разработки и стандартизации новых плагинов реализована команда:

```bash
sboxctl plugin-template <type> <ClassName> [--output-dir ./src/sboxmgr/subscription/<type>s/]
```
- `<type>`: fetcher, parser, validator
- `<ClassName>`: имя класса (CamelCase, без суффикса)
- `--output-dir`: куда сохранить шаблон (по умолчанию — текущая папка)

**Что генерируется:**
- Шаблон класса с Google-style docstring и заглушкой метода (`fetch`, `parse`, `validate`)
- Пример unit-теста для pytest (test_<classname>.py)
- Импорт базового класса и моделей

**Best practices:**
- После генерации — зарегистрируйте плагин через `@register("type")` в нужном registry.
- Проверьте/дополните docstring, добавьте edge-тесты.
- Для внешних плагинов используйте entry points (см. ADR-0002).
- Для автодокументации и автотестов используйте шаблонные тесты как основу.

**Пример:**
```bash
sboxctl plugin-template fetcher MyCustomFetcher --output-dir ./src/sboxmgr/subscription/fetchers/
```

**Результат:**
- `mycustomfetcher.py` — шаблон класса
- `test_mycustomfetcher.py` — шаблон теста

**Расширение:**
- Для новых типов (exporter, postprocessor и др.) — расширяйте CLI-генератор по аналогии.
- Документируйте публичные методы и добавляйте примеры использования.
