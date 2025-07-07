# Демонстрация CLI sboxmgr

Краткий гид по основным сценариям использования CLI (`sboxctl`).

---

## 🎯 Что умеет CLI
- Выбирать и применять прокси-серверы из удалённой конфигурации
- Исключать серверы из выбора (и управлять exclusions)
- Предварительно просматривать изменения конфига без записи файлов (dry-run)
- Список всех доступных серверов с деталями
- Управлять всем через современный CLI, удобный для скриптов

---

## 🚀 1. Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env  # Отредактируйте при необходимости
sboxctl export -u "https://example.com/proxy-config.json" --index 1
```

---

## 🏁 2. Типовые сценарии CLI

### Применить сервер по индексу
```bash
sboxctl export -u "https://example.com/proxy-config.json" --index 1
# Вывод: создан config.json для выбранного сервера
```

### Предпросмотр конфига (dry-run, без изменений файлов)
```bash
sboxctl export -u "https://example.com/proxy-config.json" --index 1 --dry-run
# Вывод: конфиг напечатан в stdout, файлы не изменяются
```

### Список всех доступных серверов
```bash
sboxctl list-servers -u "https://example.com/proxy-config.json"
# Вывод: таблица серверов с индексами, remarks, протоколами и т.д.
```

### Исключить сервер по индексу
```bash
sboxctl exclusions -u "https://example.com/proxy-config.json" --add 2
# Вывод: сервер с индексом 2 добавлен в exclusions.json
```

### Удалить сервер из exclusions
```bash
sboxctl exclusions -u "https://example.com/proxy-config.json" --remove 2
# Вывод: сервер с индексом 2 удалён из exclusions.json
```

### Посмотреть текущие exclusions
```bash
sboxctl exclusions --view
# Вывод: список исключённых серверов
```

### Очистить exclusions
```bash
sboxctl exclusions --clear --yes
# Вывод: exclusions.json очищен
```

### Выбрать сервер по имени
```bash
sboxctl export -u "https://example.com/proxy-config.json" --remarks "Быстрый сервер"
# Вывод: конфиг создан для сервера с указанным именем
```

### Продвинутая конфигурация
```bash
# SOCKS прокси на порту 1080
sboxctl export -u "https://example.com/proxy-config.json" --index 1 \
  --inbound-types socks --socks-port 1080

# Вся маршрутизация через прокси
sboxctl export -u "https://example.com/proxy-config.json" --index 1 \
  --final-route proxy
```

---

## ⚠️ 3. Примеры ошибок и их обработка

### Не указан или пустой URL
```bash
sboxctl export -u ""
# Вывод: Ошибка: требуется URL (код возврата 1)
```

### Попытка выбрать несуществующий сервер
```bash
sboxctl export -u "https://example.com/proxy-config.json" --index 99
# Вывод: Ошибка: сервер с индексом 99 не найден (код возврата 1)
```

### Неверный формат URL
```bash
sboxctl export -u "invalid-url"
# Вывод: Ошибка: неверный формат URL (код возврата 1)
```

---

## 🛠️ 4. Советы и best practices
- Используйте `.env.example` для настройки всех путей, URL и уровня debug.
- Для скриптов проверяйте коды возврата: `0` = успех, `1` = ошибка.
- Используйте `--dry-run` для предварительного просмотра изменений.
- Все команды CLI поддерживают `--help` для справки.
- **Если не удаётся удалить exclusion по индексу или ID, используйте `sboxctl exclusions --clear --yes` для полной очистки или вручную отредактируйте exclusions.json.**
- Для продвинутого использования и разработки см. [README.md](README.md) и [DEVELOPMENT.md](DEVELOPMENT.md).

---

## 📎 Ссылки
- [README.md](README.md) — полная документация
- [.env.example](../../.env.example) — все переменные окружения
- [CHANGELOG.md](CHANGELOG.md) — последние изменения

---

> Хотите визуальную демонстрацию? Предложите GIF или видео в issues!
