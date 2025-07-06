# Справочник CLI

Этот документ содержит полный справочник всех команд и опций CLI SBoxMgr.

## Обзор

SBoxMgr предоставляет командную строку для управления конфигурациями sing-box, подписками и профилями.

## Глобальные опции

Все команды поддерживают эти глобальные опции:

- `--debug`, `-d <уровень>`: Установить уровень отладки (0-3)
- `--help`, `-h`: Показать справку

## Команды

### Управление серверами

#### `sboxctl list-servers`
Вывести список всех серверов из подписки.

**Опции:**
- `-u, --url <url>`: URL подписки (**обязательно**)
- `--format <формат>`: Формат вывода (table, json, yaml)
- `--filter <фильтр>`: Фильтр серверов по критериям

**Пример:**
```bash
sboxctl list-servers -u "https://example.com/proxy.json"
```

### Экспорт конфигурации

#### `sboxctl export`
Экспортировать конфигурацию sing-box.

**Опции:**
- `-u, --url <url>`: URL подписки (**обязательно**)
- `--index <номер>`: Индекс сервера
- `--remarks <имя>`: Имя/заметка сервера
- `--dry-run`: Проверить без записи файлов
- `--inbound-types <типы>`: Типы inbound (tun, socks, http, tproxy)
- `--socks-port <порт>`: Порт SOCKS-прокси
- `--socks-listen <адрес>`: Адрес для SOCKS
- `--socks-auth <пользователь:пароль>`: Аутентификация SOCKS
- `--http-port <порт>`: Порт HTTP-прокси
- `--http-listen <адрес>`: Адрес для HTTP
- `--http-auth <пользователь:пароль>`: Аутентификация HTTP
- `--tproxy-port <порт>`: Порт TPROXY
- `--tproxy-listen <адрес>`: Адрес TPROXY
- `--tun-address <CIDR>`: Адрес интерфейса TUN
- `--tun-mtu <MTU>`: MTU для TUN
- `--tun-stack <stack>`: Стек TUN (system, gvisor)
- `--dns-mode <режим>`: Режим DNS (system, tunnel, off)
- `--final-route <маршрут>`: Конечный маршрут
- `--exclude-outbounds <типы>`: Исключить outbound-типы

**Примеры:**
```bash
# Базовый экспорт
sboxctl export -u "https://example.com/proxy.json" --index 1

# С кастомным inbound
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --inbound-types socks --socks-port 1080

# Dry run
sboxctl export -u "https://example.com/proxy.json" --index 1 --dry-run
```

### Управление исключениями

#### `sboxctl exclusions`
Управление списком исключённых серверов.

**Опции:**
- `-u, --url <url>`: URL подписки
- `--add <индекс>`: Добавить сервер в исключения
- `--remove <индекс>`: Удалить сервер из исключений
- `--view`: Показать текущие исключения
- `--clear`: Очистить все исключения

**Примеры:**
```bash
# Добавить сервер в исключения
sboxctl exclusions -u "https://example.com/proxy.json" --add 3

# Удалить сервер из исключений
sboxctl exclusions -u "https://example.com/proxy.json" --remove 3

# Показать исключения
sboxctl exclusions --view

# Очистить все исключения
sboxctl exclusions --clear --yes
```

### Управление конфигурацией

#### `sboxctl config`
Команды для работы с конфигурацией.

**Подкоманды:**
- `validate`: Проверить конфигурационный файл
- `dump`: Вывести разрешённую конфигурацию
- `schema`: Сгенерировать JSON схему
- `env-info`: Показать информацию об окружении

**Примеры:**
```bash
# Проверить конфиг
sboxctl config validate config.json

# Вывести конфигурацию
sboxctl config dump --format json

# Сгенерировать схему
sboxctl config schema --output schema.json
```

### Управление профилями

#### `sboxctl profile`
Команды для работы с профилями.

**Подкоманды:**
- `list`: Список доступных профилей
- `apply`: Применить профиль к конфигурации
- `validate`: Проверить профиль
- `explain`: Объяснить настройки профиля
- `diff`: Показать различия между профилями
- `switch`: Переключиться на другой профиль

**Примеры:**
```bash
# Список профилей
sboxctl profile list

# Применить профиль
sboxctl profile apply profile.json

# Проверить профиль
sboxctl profile validate profile.json

# Переключить профиль
sboxctl profile switch work
```

### Управление политиками

#### `sboxctl policy`
Команды для работы с политиками.

**Подкоманды:**
- `list`: Список доступных политик
- `test`: Проверить политики с контекстом
- `audit`: Аудит серверов по политикам
- `enable`: Включить политики
- `disable`: Отключить политики
- `info`: Показать информацию о системе политик

**Примеры:**
```bash
# Список политик
sboxctl policy list

# Проверить политики
sboxctl policy test --profile profile.json

# Аудит серверов
sboxctl policy audit --servers servers.json
```

### Управление языками

#### `sboxctl lang`
Команды для управления языком интерфейса.

**Опции:**
- `--set <код>`: Установить язык (en, ru, de и др.)
- `--list`: Показать доступные языки

**Примеры:**
```bash
# Установить язык
sboxctl lang --set ru

# Показать языки
sboxctl lang --list
```

### Разработка плагинов

#### `sboxctl plugin-template`
Генерация шаблона плагина.

**Опции:**
- `<type>`: Тип плагина (fetcher, parser, exporter, validator)
- `<ClassName>`: Имя класса (CamelCase)
- `--output-dir <путь>`: Папка для вывода

**Пример:**
```bash
sboxctl plugin-template fetcher MyCustomFetcher --output-dir ./plugins/
```

## Переменные окружения

SBoxMgr поддерживает настройку через переменные окружения. Создайте файл `.env` в корне проекта:

```bash
# Путь к файлу конфигурации (по умолчанию: ./config.json)
SBOXMGR_CONFIG_FILE=/etc/sing-box/config.json

# Путь к лог-файлу
SBOXMGR_LOG_FILE=./sboxmgr.log

# Файл исключений
SBOXMGR_EXCLUSION_FILE=./exclusions.json

# Язык (en, ru, de, zh и др.)
SBOXMGR_LANG=ru
```

## Примечания
- Все команды поддерживают `--help` для вывода справки.
- Для подробных примеров и сценариев см. [SHOWCASE.md](SHOWCASE.md).
- Для продвинутых настроек и разработки см. [README.md](README.md) и [DEVELOPMENT.md](DEVELOPMENT.md).

---

**Последнее обновление:** 2025-07-05
