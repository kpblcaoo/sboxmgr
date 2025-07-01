# sboxmgr Quick Reference Card

## 🚀 Быстрый старт

```bash
# Простая команда
python -m sboxmgr.cli export --inbound-types tun

# С параметрами
python -m sboxmgr.cli export \
  --url "$SUB_URL" \
  --inbound-types tun,socks \
  --socks-auth user:pass \
  --postprocessors geo_filter
```

## 📋 Основные компоненты

| Компонент | Файл | Назначение |
|-----------|------|------------|
| CLI Entry | `cli/commands/export.py` | Парсинг команд, координация |
| InboundBuilder | `cli/inbound_builder.py` | Создание ClientProfile из CLI |
| Fetchers | `subscription/fetchers/` | Загрузка подписок (URL/File/API) |
| Parsers | `subscription/parsers/` | Парсинг форматов (YAML/JSON/base64) |
| Middleware | `subscription/middleware/` | Обогащение данных |
| Postprocessors | `subscription/postprocessors/` | Фильтрация и сортировка |
| Exporters | `subscription/exporters/` | Генерация sing-box конфига |
| Policies | `policies/` | Политики безопасности |

## 🔄 Поток данных

```
CLI → InboundBuilder → Fetcher → Parser → Middleware → Postprocessors → Exporter → Output
```

## 📝 Доступные параметры

### Inbound Types
- `tun` - TUN интерфейс (системная маршрутизация)
- `socks` - SOCKS5 прокси сервер
- `http` - HTTP прокси сервер
- `tproxy` - Transparent proxy (Linux)

### Postprocessors
- `geo_filter` - Фильтрация по странам
- `tag_filter` - Фильтрация по тегам
- `latency_sort` - Сортировка по пингу
- `duplicate_removal` - Удаление дубликатов

### Middleware
- `logging` - Логирование операций
- `enrichment` - Обогащение метаданных

## 🛡️ Безопасность по умолчанию

- SOCKS/HTTP: bind на `127.0.0.1`
- Порты: только unprivileged (1024-65535)
- TPROXY: bind на `0.0.0.0` (требуется для функциональности)
- Предупреждения при внешнем bind

## 🔧 Примеры конфигураций

### Домашний пользователь
```bash
--inbound-types tun
```

### Разработчик
```bash
--inbound-types socks,http \
--socks-port 1080 \
--http-port 8080
```

### Сервер
```bash
--inbound-types socks,http,tproxy \
--socks-listen "0.0.0.0" \
--socks-auth admin:password \
--http-listen "0.0.0.0" \
--postprocessors geo_filter
```

## 🚨 Частые проблемы

**Q: Серверы не появляются**
```bash
# Добавить логирование
--middleware logging
```

**Q: Нужна фильтрация**
```bash
# Исключить российские серверы
--postprocessors geo_filter
```

**Q: Ошибка bind permission**
```bash
# Использовать unprivileged порты
--socks-port 1080  # не 80
```

**Q: Внешний доступ к прокси**
```bash
# Явно указать bind на все интерфейсы
--socks-listen "0.0.0.0"
```

## 📊 Отладка

```bash
# Полное логирование
--middleware logging --debug 2

# Проверка без сохранения
--dry-run

# Валидация результата
sing-box check -c output.json
```

## 🎯 Архитектурные принципы

1. **Модульность** - каждый компонент независим
2. **Безопасность** - secure by default
3. **Расширяемость** - легко добавлять новые форматы/протоколы
4. **Совместимость** - обратная совместимость с профилями
5. **Валидация** - проверка на каждом уровне 