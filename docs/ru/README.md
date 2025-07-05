# SBoxMgr - Менеджер конфигураций Sing-box

[![Build Status](https://github.com/kpblcaoo/update-singbox/actions/workflows/ci-dev.yml/badge.svg)](https://github.com/kpblcaoo/update-singbox/actions)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/kpblcaoo/update-singbox/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Python CLI инструмент для управления конфигурациями прокси [sing-box](https://sing-box.sagernet.org/). Автоматически загружает списки серверов, применяет исключения, генерирует конфиги и поддерживает продвинутую маршрутизацию.

## 🚀 Быстрый старт (3 шага)

### 1. Установка
```bash
# Клонировать и установить
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install .
```

### 2. Получить URL прокси
Вам нужен URL, который предоставляет совместимую с sing-box конфигурацию (Clash, sing-box JSON и т.д.). Обычные источники:
- Ссылка на подписку вашего VPN провайдера
- URL конфигурации Clash
- Файл конфигурации sing-box

### 3. Сгенерировать конфиг
```bash
# Список доступных серверов
sboxctl list-servers -u "ВАШ_URL_ПРОКСИ_ЗДЕСЬ"

# Сгенерировать конфиг для сервера #1
sboxctl export -u "ВАШ_URL_ПРОКСИ_ЗДЕСЬ" --index 1

# Запустить sing-box с сгенерированным конфигом
sing-box run -c config.json
```

Всё! Ваш sing-box теперь работает с выбранным сервером.

## ✨ Ключевые возможности

- **Простой CLI**: Одна команда для генерации рабочих конфигов sing-box
- **Множество протоколов**: VLESS, Shadowsocks, VMess, Trojan, TUIC, Hysteria2
- **Умная маршрутизация**: Прямая маршрутизация для российских доменов, прокси для остальных
- **Управление серверами**: Список, выбор и исключение серверов
- **Гибкий ввод**: Поддержка Clash, sing-box JSON и других форматов
- **Готов к продакшену**: 90%+ покрытие тестами, комплексная обработка ошибок

## 📖 Обычное использование

### Базовые операции
```bash
# Список всех доступных серверов
sboxctl list-servers -u "https://example.com/proxy.json"

# Сгенерировать конфиг для конкретного сервера
sboxctl export -u "https://example.com/proxy.json" --index 2

# Сгенерировать конфиг для сервера по имени
sboxctl export -u "https://example.com/proxy.json" --remarks "Быстрый сервер"

# Предварительный просмотр конфига без сохранения (dry-run)
sboxctl export -u "https://example.com/proxy.json" --index 1 --dry-run
```

### Управление серверами
```bash
# Добавить сервер в исключения (не будет использоваться)
sboxctl exclusions -u "https://example.com/proxy.json" --add 3

# Удалить сервер из исключений
sboxctl exclusions -u "https://example.com/proxy.json" --remove 3

# Просмотр текущих исключений
sboxctl exclusions --view

# Очистить все исключения
sboxctl clear-exclusions
```

### Продвинутая конфигурация
```bash
# Настроить кастомный inbound (SOCKS прокси на порту 1080)
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --inbound-types socks --socks-port 1080

# Установить кастомную маршрутизацию (весь трафик через прокси)
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --final-route proxy

# Исключить конкретные типы outbound
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --exclude-outbounds block,dns
```

## ⚙️ Конфигурация

### Переменные окружения
Создайте файл `.env` в корне проекта:

```bash
# Расположение файла конфига (по умолчанию: ./config.json)
SBOXMGR_CONFIG_FILE=/etc/sing-box/config.json

# Расположение файла логов
SBOXMGR_LOG_FILE=./sboxmgr.log

# Файл исключений
SBOXMGR_EXCLUSION_FILE=./exclusions.json

# Язык (en, ru, de, zh, и т.д.)
SBOXMGR_LANG=ru
```

### Поведение по умолчанию
- **Вывод конфига**: `./config.json` (или `SBOXMGR_CONFIG_FILE`)
- **Логирование**: `./sboxmgr.log` (или `SBOXMGR_LOG_FILE`)
- **Исключения**: `./exclusions.json` (или `SBOXMGR_EXCLUSION_FILE`)
- **Язык**: Английский (или `SBOXMGR_LANG`)

## 🔧 Продвинутые возможности

### Система плагинов
Создавайте кастомные fetchers, parsers и exporters:

```bash
# Сгенерировать шаблон плагина
sboxctl plugin-template fetcher MyCustomFetcher --output-dir ./plugins/

# Использовать кастомный плагин
sboxctl export -u "custom://my-data" --fetcher my-custom-fetcher
```

### Движок политик
Настройте политики маршрутизации:

```bash
# Список доступных политик
sboxctl policy list

# Применить гео-политику
sboxctl export -u "https://example.com/proxy.json" --index 1 \
  --policy geo-direct
```

### Интернационализация
```bash
# Установить язык
sboxctl lang --set ru

# Просмотр доступных языков
sboxctl lang
```

## 🛠 Разработка

### Настройка среды разработки
```bash
# Установить с зависимостями для разработки
pip install -e ".[dev]"

# Запустить тесты
pytest -v

# Запустить линтинг
ruff check src/

# Форматировать код
black src/
```

### Структура проекта
```
src/sboxmgr/
├── cli/          # Командная строка
├── core/         # Основная бизнес-логика
├── subscription/ # Управление подписками
├── export/       # Экспорт конфигураций
├── models/       # Модели данных
├── i18n/         # Интернационализация
└── utils/        # Утилиты
```

## 📚 Документация

- [Руководство пользователя](user-guide/) - Подробные инструкции по использованию
- [Справочник CLI](user-guide/cli-reference.md) - Полный справочник команд
- [Руководство по конфигурации](getting-started/configuration.md) - Продвинутая конфигурация
- [Безопасность](security.md) - Соображения безопасности
- [Разработка](developer/) - Руководства по разработке

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для функции
3. Внесите изменения
4. Добавьте тесты
5. Отправьте pull request

## 📜 Лицензия

Проект распространяется под лицензией MIT. Подробнее см. в LICENSE.

---

**Другие языки / Other languages**
- [English (README.md)](../../README.md) 