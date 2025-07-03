# sboxmgr Architecture Deep Dive

> **Полное техническое описание архитектуры sboxmgr от входа до выхода**

## 🎯 Общая схема потока данных

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Command   │───▶│  Configuration   │───▶│   Subscription  │
│                 │    │    Loading       │    │    Fetching     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Final Config   │◀───│   Export Layer   │◀───│   Processing    │
│   (sing-box)    │    │                  │    │    Pipeline     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📥 Входной слой (CLI Commands)

### Файл: `src/sboxmgr/cli/commands/export.py`

**Что принимает на вход:**
```bash
python -m sboxmgr.cli export \
  --url "https://example.com/subscription" \     # URL подписки
  --inbound-types tun,socks \                   # Типы inbound'ов
  --socks-port 1080 \                          # Параметры inbound'ов
  --postprocessors geo_filter \                # Постпроцессоры
  --output config.json                         # Выходной файл
```

**Приоритет источников конфигурации:**
1. `--client-profile file.json` (высший приоритет)
2. CLI параметры (`--inbound-types`, `--socks-port`, etc.)
3. `--profile profile.json` (если содержит client config)
4. Дефолтный минимальный профиль (низший приоритет)

**Что происходит внутри:**
```python
def export(...):
    # 1. Загрузка профилей и параметров
    loaded_profile = _load_profile_from_file(profile) if profile else None
    loaded_client_profile = _load_client_profile_from_file(client_profile) if client_profile else None
    
    # 2. Создание ClientProfile из CLI параметров (если нужно)
    if not loaded_client_profile and inbound_types:
        loaded_client_profile = build_client_profile_from_cli(...)
    
    # 3. Создание цепочек обработки
    postprocessor_chain = _create_postprocessor_chain(postprocessors)
    middleware_chain = _create_middleware_chain(middleware)
    
    # 4. Генерация конфигурации
    config_data = _generate_config_from_subscription(...)
    
    # 5. Сохранение результата
    _save_config_to_file(config_data, output)
```

## 🏗️ Слой построения ClientProfile

### Файл: `src/sboxmgr/cli/inbound_builder.py`

**InboundBuilder - паттерн Builder для создания профилей:**

```python
# Пример использования
builder = InboundBuilder()
profile = (builder
    .add_tun(address="198.18.0.1/16", mtu=1500)
    .add_socks(port=1080, auth="user:pass")
    .set_dns_mode("tunnel")
    .build())
```

**Поддерживаемые типы inbound'ов:**

1. **TUN** (`add_tun`):
   - `address`: IP адреса интерфейса (default: `["198.18.0.1/16"]`)
   - `mtu`: MTU значение (default: `1500`, range: `576-9000`)
   - `stack`: Сетевой стек (`system`, `gvisor`, `mixed`, default: `mixed`)
   - `auto_route`: Автоматическая маршрутизация (default: `True`)

2. **SOCKS** (`add_socks`):
   - `port`: Порт (default: `1080`, range: `1024-65535`)
   - `listen`: Адрес привязки (default: `"127.0.0.1"` для безопасности)
   - `auth`: Аутентификация в формате `"user:pass"` (optional)

3. **HTTP** (`add_http`):
   - `port`: Порт (default: `8080`, range: `1024-65535`)
   - `listen`: Адрес привязки (default: `"127.0.0.1"` для безопасности)
   - `auth`: Аутентификация в формате `"user:pass"` (optional)

4. **TPROXY** (`add_tproxy`):
   - `port`: Порт (default: `7895`, range: `1024-65535`)
   - `listen`: Адрес привязки (default: `"0.0.0.0"` - нужен для TPROXY)
   - `network`: Тип сети (`tcp`, `udp`, `tcp,udp`, default: `tcp`)

**Безопасность по умолчанию:**
- SOCKS/HTTP привязываются к localhost (`127.0.0.1`)
- Валидация портов (только unprivileged: 1024-65535)
- Предупреждения при привязке к `0.0.0.0`

## 🌐 Слой загрузки подписок

### Файл: `src/sboxmgr/subscription/fetchers/`

**Доступные фетчеры:**

1. **URLFetcher** (`url_fetcher.py`):
   - HTTP/HTTPS загрузка
   - Поддержка User-Agent
   - Автоматическая декомпрессия (gzip, deflate)
   - Timeout handling

2. **FileFetcher** (`file_fetcher.py`):
   - Локальные файлы
   - Поддержка относительных путей

3. **ApiFetcher** (`apifetcher.py`):
   - API endpoints с токенами
   - JSON response parsing

**Пример работы URLFetcher:**
```python
fetcher = URLFetcher()
raw_data = fetcher.fetch("https://example.com/sub", user_agent="sboxmgr/1.0")
# raw_data содержит сырые данные подписки (YAML, JSON, base64, etc.)
```

## 🔍 Слой парсинга подписок

### Файл: `src/sboxmgr/subscription/parsers/`

**Автоопределение формата:**
```python
def _detect_source_type(raw_data: bytes) -> str:
    """Автоматически определяет тип данных подписки."""
    # 1. Проверка на base64
    # 2. Проверка на JSON
    # 3. Проверка на YAML
    # 4. Fallback на URI list
```

**Доступные парсеры:**

1. **Base64Parser** (`base64_parser.py`):
   - Декодирует base64 данные
   - Парсит URI списки внутри

2. **ClashParser** (`clash_parser.py`):
   - YAML формат Clash
   - Извлекает proxies секцию
   - Конвертирует в ParsedServer объекты

3. **JsonParser** (`json_parser.py`):
   - JSON формат подписок
   - Поддержка вложенных структур

4. **URIListParser** (`uri_list_parser.py`):
   - Простые списки URI (ss://, vmess://, etc.)
   - Построчный парсинг

5. **SingboxParser** (`singbox_parser.py`):
   - Нативный sing-box формат
   - Извлекает outbounds

**Результат парсинга:**
```python
class ParsedServer:
    protocol: str           # "shadowsocks", "vmess", "vless", etc.
    server: str            # IP или домен
    port: int              # Порт сервера
    meta: Dict[str, Any]   # Все остальные параметры (пароли, шифры, etc.)
```

## ⚙️ Слой обработки (Middleware)

### Файл: `src/sboxmgr/subscription/middleware/`

**Доступные middleware:**

1. **LoggingMiddleware** (`logging.py`):
   - Логирование всех операций
   - Подсчет статистики серверов
   - Debug информация

2. **EnrichmentMiddleware** (`enrichment.py`):
   - Обогащение метаданных серверов
   - GeoIP определение стран
   - Добавление тегов и меток

**Порядок выполнения:**
```
Raw Data → Parsing → [Middleware Chain] → Parsed Servers
                     ↓
              1. Logging (статистика)
              2. Enrichment (геоданные)
```

## 🎛️ Слой постобработки (Postprocessors)

### Файл: `src/sboxmgr/subscription/postprocessors/`

**Доступные постпроцессоры:**

1. **GeoFilterPostprocessor** (`geo_filter.py`):
   ```python
   # Конфигурация
   config = {
       "exclude": ["RU", "CN"],        # Исключить страны
       "include": ["US", "DE"],        # Включить только эти страны
       "exclude_keywords": ["expired"] # Исключить по ключевым словам
   }
   ```

2. **TagFilterPostprocessor** (`tag_filter.py`):
   ```python
   # Конфигурация
   config = {
       "exclude_tags": ["free", "slow"],
       "only_tags": ["premium", "fast"]
   }
   ```

3. **LatencySortPostprocessor** (`latency_sort.py`):
   - Сортировка по пингу (если доступно)
   - Удаление недоступных серверов

4. **DuplicateRemovalPostprocessor** (`duplicate_removal.py`):
   - Удаление дубликатов по server:port
   - Приоритизация по качеству

**Цепочка выполнения:**
```
Parsed Servers → [Postprocessor Chain] → Filtered Servers
                 ↓
         1. GeoFilter (фильтрация по странам)
         2. TagFilter (фильтрация по тегам)
         3. LatencySort (сортировка)
         4. DuplicateRemoval (дедупликация)
```

**Как добавить постпроцессор в CLI:**
```bash
--postprocessors geo_filter,tag_filter,latency_sort
```

## 🚀 Слой экспорта

### Файл: `src/sboxmgr/subscription/exporters/singbox_exporter.py`

**Основная функция экспорта:**
```python
def singbox_export(
    servers: List[ParsedServer],
    routes,
    client_profile: Optional[ClientProfile] = None
) -> dict:
    """Экспортирует серверы в sing-box конфигурацию."""
```

**Что происходит внутри:**

1. **Создание outbound'ов:**
   ```python
   outbounds = []
   proxy_tags = []
   
   for server in servers:
       outbound = _create_outbound_from_server(server)
       outbounds.append(outbound)
       proxy_tags.append(outbound["tag"])
   ```

2. **Создание URLTest группы:**
   ```python
   urltest_outbound = {
       "type": "urltest",
       "tag": "auto",
       "outbounds": proxy_tags,
       "url": "https://www.gstatic.com/generate_204",
       "interval": "5m"
   }
   ```

3. **Генерация inbound'ов:**
   ```python
   if client_profile:
       config["inbounds"] = generate_inbounds(client_profile)
   ```

4. **Создание маршрутизации:**
   ```python
   config["route"] = {
       "rules": [
           {"geoip": ["ru"], "outbound": "direct"},
           {"domain_suffix": [".ru"], "outbound": "direct"}
       ],
       "rule_set": [...],
       "final": "auto"
   }
   ```

**Поддерживаемые протоколы outbound'ов:**
- Shadowsocks (`ss://`)
- VMess (`vmess://`)
- VLESS (`vless://`)
- Trojan (`trojan://`)
- Hysteria (`hysteria://`)
- TUIC (`tuic://`)

**Специальная обработка:**

1. **TLS/Reality конфигурация:**
   ```python
   def _process_tls_config(outbound, meta, protocol_type):
       if meta.get("reality-opts"):
           outbound["tls"] = {
               "enabled": True,
               "reality": {
                   "enabled": True,
                   "public_key": meta["reality-opts"]["public-key"],
                   "short_id": meta["reality-opts"]["short-id"]
               }
           }
   ```

2. **Генерация inbound'ов:**
   ```python
   def generate_inbounds(profile: ClientProfile) -> list:
       inbounds = []
       for inbound in profile.inbounds:
           if inbound.type == "tun":
               inb = {
                   "type": "tun",
                   "tag": inbound.options.get("tag", "tun-in"),
                   "address": inbound.options.get("address", ["198.18.0.1/16"]),
                   "mtu": inbound.options.get("mtu", 1500)
               }
           elif inbound.type == "socks":
               inb = {
                   "type": "socks",
                   "tag": inbound.options.get("tag", "socks-in"),
                   "listen": inbound.listen,
                   "listen_port": inbound.port
               }
           # ... остальные типы
           inbounds.append(inb)
       return inbounds
   ```

## 🛡️ Слой политик безопасности

### Файл: `src/sboxmgr/policies/`

**Доступные политики:**

1. **SecurityPolicy** (`security_policy.py`):
   - Проверка безопасных портов
   - Валидация bind адресов
   - Блокировка подозрительных конфигураций

2. **GeoPolicy** (`geo_policy.py`):
   - Фильтрация по географии
   - Блокировка определенных стран
   - Whitelist режим

**Пример работы политик:**
```python
# В процессе обработки серверов
for server in servers:
    for policy in active_policies:
        if not policy.allow(server):
            logger.info(f"Server {server.server} denied by policy {policy.name}")
            continue  # Сервер отклонен политикой
```

## 📊 Слой валидации

### Файл: `src/sboxmgr/subscription/validators/`

**Доступные валидаторы:**

1. **BaseValidator** (`base.py`):
   - Базовая структурная валидация
   - Проверка обязательных полей

2. **GeoValidator** (`geovalidator.py`):
   - Валидация географических данных
   - Проверка ISO кодов стран

3. **ProtocolValidator** (`protocol_validator.py`):
   - Валидация протокол-специфичных параметров
   - Проверка шифров и методов

## 🗂️ Слой моделей данных

### Файл: `src/sboxmgr/subscription/models.py`

**Основные модели:**

1. **ParsedServer**:
   ```python
   class ParsedServer(BaseModel):
       protocol: str
       server: str
       port: int
       meta: Dict[str, Any]
   ```

2. **ClientProfile**:
   ```python
   class ClientProfile(BaseModel):
       inbounds: List[InboundProfile]
       dns_mode: str = "system"
   ```

3. **InboundProfile**:
   ```python
   class InboundProfile(BaseModel):
       type: str  # "tun", "socks", "http", "tproxy"
       listen: Optional[str] = None
       port: Optional[int] = None
       options: Dict[str, Any] = {}
   ```

## 🔧 Конфигурация по умолчанию

**Постпроцессоры по умолчанию:**
- Никаких постпроцессоров не применяется автоматически
- Нужно явно указывать через `--postprocessors`

**Доступные постпроцессоры:**
```bash
--postprocessors geo_filter          # Географическая фильтрация
--postprocessors tag_filter          # Фильтрация по тегам
--postprocessors latency_sort        # Сортировка по пингу
--postprocessors duplicate_removal   # Удаление дубликатов
```

**Middleware по умолчанию:**
- Никакого middleware не применяется автоматически
- Нужно явно указывать через `--middleware`

**Доступные middleware:**
```bash
--middleware logging                 # Логирование операций
--middleware enrichment              # Обогащение метаданных
```

**Настройки по умолчанию для inbound'ов:**
- TUN: `198.18.0.1/16`, MTU 1500, stack mixed
- SOCKS: порт 1080, bind на 127.0.0.1
- HTTP: порт 8080, bind на 127.0.0.1  
- TPROXY: порт 7895, bind на 0.0.0.0

## 🔄 Полный цикл обработки

```
1. CLI Parsing
   ├── URL extraction (env vars, --url)
   ├── Profile loading (--profile, --client-profile)
   └── CLI parameters (--inbound-types, --socks-port, etc.)

2. Configuration Building
   ├── ClientProfile creation (InboundBuilder)
   ├── Postprocessor chain setup
   └── Middleware chain setup

3. Subscription Processing
   ├── Fetching (URLFetcher, FileFetcher)
   ├── Format detection (auto-detect)
   ├── Parsing (ClashParser, JsonParser, etc.)
   └── Server object creation (ParsedServer)

4. Data Processing Pipeline
   ├── Middleware execution (logging, enrichment)
   ├── Policy enforcement (security, geo)
   ├── Postprocessing (filtering, sorting)
   └── Validation (structure, protocols)

5. Export Generation
   ├── Outbound creation (protocol-specific)
   ├── Inbound generation (from ClientProfile)
   ├── Routing rules (geo-based, rule_sets)
   └── Final config assembly (sing-box format)

6. Output
   ├── Config validation (sing-box check)
   ├── File writing (JSON format)
   └── Success reporting
```

## 🤔 Частые вопросы

**Q: Какие постпроцессоры доступны?**
A: `geo_filter`, `tag_filter`, `latency_sort`, `duplicate_removal`

**Q: Как узнать какие серверы были отфильтрованы?**
A: Включить middleware logging: `--middleware logging`

**Q: Можно ли комбинировать --client-profile и CLI параметры?**
A: CLI параметры имеют приоритет над файлом профиля

**Q: Как работает geo_filter?**
A: Фильтрует серверы по ISO кодам стран в meta['country'] или определяет по IP

**Q: Почему SOCKS привязывается к 127.0.0.1?**
A: Безопасность по умолчанию. Используйте `--socks-listen "0.0.0.0"` для внешнего доступа

Это полное техническое описание архитектуры sboxmgr от входа до выхода! 🚀 