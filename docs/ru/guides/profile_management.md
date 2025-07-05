# Профили

Профили в SBoxMgr позволяют настраивать генерацию конфигурации, фильтрацию и настройки экспорта с помощью JSON-файлов конфигурации.

## Обзор

Профиль — это JSON-файл конфигурации, который определяет:
- Настройки и предпочтения подписки
- Конфигурацию экспорта и маршрутизации
- Правила фильтрации и исключения
- Пользовательские middleware и постпроцессоры
- Политики безопасности

## Структура профиля

```json
{
  "id": "my-profile",
  "name": "Мой пользовательский профиль",
  "description": "Пользовательский профиль для моих нужд",
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30
  },
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http"],
    "socks_port": 1080,
    "http_port": 8080
  },
  "filter": {
    "exclude_tags": ["blocked"],
    "only_tags": ["premium"],
    "geo_filter": {
      "include": ["US", "CA"],
      "exclude": ["CN", "RU"]
    }
  },
  "routing": {
    "final": "proxy",
    "rules": [
      {
        "domain_suffix": [".ru"],
        "outbound": "direct"
      }
    ]
  }
}
```

## Секции профиля

### Секция подписки

Определяет источник подписки и настройки:

```json
{
  "subscription": {
    "url": "https://example.com/subscription",
    "user_agent": "Custom User-Agent",
    "timeout": 30,
    "retries": 3,
    "headers": {
      "Authorization": "Bearer token"
    }
  }
}
```

**Опции:**
- `url`: URL подписки
- `user_agent`: Пользовательский заголовок User-Agent
- `timeout`: Таймаут запроса в секундах
- `retries`: Количество попыток повтора
- `headers`: Пользовательские HTTP-заголовки

### Секция экспорта

Настраивает поведение экспорта и настройки входящих соединений:

```json
{
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http", "tun"],
    "socks_port": 1080,
    "socks_listen": "127.0.0.1",
    "http_port": 8080,
    "tun_address": "172.19.0.1/30",
    "final_route": "proxy"
  }
}
```

**Опции:**
- `format`: Формат экспорта (sing-box)
- `inbound_types`: Список типов входящих соединений для включения
- `socks_port`, `http_port`, `tproxy_port`: Номера портов
- `socks_listen`, `http_listen`: Адреса прослушивания
- `tun_address`: Адрес TUN-интерфейса
- `final_route`: Финальный пункт назначения маршрутизации

### Секция фильтрации

Определяет правила фильтрации серверов:

```json
{
  "filter": {
    "exclude_tags": ["blocked", "slow"],
    "only_tags": ["premium", "fast"],
    "geo_filter": {
      "include": ["US", "CA"],
      "exclude": ["CN", "RU"]
    }
  }
}
```

**Опции:**
- `exclude_tags`: Теги для исключения
- `only_tags`: Теги для включения (белый список)
- `geo_filter`: Правила географической фильтрации

### Секция маршрутизации

Настраивает правила маршрутизации:

```json
{
  "routing": {
    "final": "proxy",
    "rules": [
      {
        "domain_suffix": [".ru", ".рф"],
        "outbound": "direct"
      },
      {
        "ip_is_private": true,
        "outbound": "direct"
      }
    ]
  }
}
```

## Управление профилями

### Список профилей

```bash
sboxctl profile list
```

### Применение профиля

```bash
sboxctl profile apply --name my-profile
```

### Валидация профиля

```bash
sboxctl profile validate --file profile.json
```

### Объяснение профиля

```bash
sboxctl profile explain --name my-profile
```

### Показать различия между профилями

```bash
sboxctl profile diff --name profile1 --name profile2
```

## Использование профилей

### С командой экспорта

```bash
# Применить профиль и экспортировать
sboxctl profile apply --name my-profile
sboxctl export -u "https://example.com/subscription" --index 1

# Или использовать профиль напрямую
sboxctl export -u "https://example.com/subscription" --index 1 \
  --inbound-types socks --socks-port 1080
```

### Примеры профилей

#### Базовый домашний профиль
```json
{
  "id": "home",
  "name": "Домашний профиль",
  "subscription": {
    "url": "https://example.com/subscription"
  },
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks"],
    "socks_port": 1080
  }
}
```

#### Профиль разработчика
```json
{
  "id": "developer",
  "name": "Профиль разработчика",
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http"],
    "socks_port": 1080,
    "http_port": 8080
  },
  "filter": {
    "exclude_tags": ["slow"]
  }
}
```

#### Серверный профиль
```json
{
  "id": "server",
  "name": "Серверный профиль",
  "export": {
    "format": "sing-box",
    "inbound_types": ["socks", "http", "tproxy"],
    "socks_listen": "0.0.0.0",
    "http_listen": "0.0.0.0",
    "socks_auth": "admin:password"
  },
  "routing": {
    "final": "proxy"
  }
}
```

## Расположение профилей

Профили обычно хранятся в:
- `~/.config/sboxmgr/profiles/` (Linux/macOS)
- `%APPDATA%\sboxmgr\profiles\` (Windows)
- `./profiles/` (текущая директория)

## Переменные окружения

Установите переменные окружения, связанные с профилями:

```bash
# Директория профилей
export SBOXMGR_PROFILE_DIR="~/.config/sboxmgr/profiles"

# Профиль по умолчанию
export SBOXMGR_DEFAULT_PROFILE="home"
```

## См. также

- [Справочник CLI](../cli_reference.md) - Интерфейс командной строки
- [Подписки](../subscriptions.md) - Управление подписками
- [Конфигурация](../configuration.md) - Системная конфигурация 