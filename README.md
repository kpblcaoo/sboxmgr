# update-singbox

Скрипт на Python для автоматизации обновления конфигураций [sing-box](https://sing-box.sagernet.org/), универсальной прокси-платформы. Инструмент загружает данные о прокси-серверах по указанному URL и применяет их к конфигурации sing-box, поддерживая различные протоколы и правила маршрутизации.

---

## ✨ Возможности

- Загрузка и применение конфигураций прокси-серверов с указанного URL.
- Поддерживаемые протоколы: **VLESS**, **Shadowsocks**, **VMess**, **Trojan**, **TUIC**, **Hysteria2**.
- Прямая маршрутизация для российских доменов (`.ru`, `.рф`, ВКонтакте, Яндекс и др.) и `geoip-ru`, остальной трафик через прокси.
- Логирование обновлений в `/var/log/update-singbox.log` с ротацией при достижении 1 МБ.
- Создание резервных копий конфигурации перед обновлением.
- Интеграция с `cron` для автоматических обновлений.
- Поддержка прокси для загрузки конфигураций через опцию `--proxy`.
- Уровни детализации логов через опцию `--debug`.
---

## 🚀 Установка

### Клонирование репозитория

```bash
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
```

### Установка зависимостей

- **Python 3.10 или новее** (необходим для конструкции `match`).
- **sing-box** (см. [инструкции по установке](https://sing-box.sagernet.org/guide/installation/)).
- **Библиотека Python requests с поддержкой SOCKS** (`requests[socks]`).

**Пример для Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip
pip install -r requirements.txt
```

### Копирование шаблона конфигурации (опционально)

```bash
sudo mkdir -p /etc/sing-box
sudo cp config.template.json /etc/sing-box/
```

### Назначение прав на выполнение скрипта

```bash
chmod +x update-singbox.py
```

---

## ⚙️ Использование

Запустите скрипт, указав URL с конфигурацией прокси-серверов:

```bash
./update-singbox.py -u https://example.com/proxy-config.json
```

### Опции

| Опция          | Описание                                              |
| -------------- | ----------------------------------------------------- |
| `-u <URL>`     | URL конфигурации прокси (**обязательно**)            |
| `-r <remarks>` | Выбор сервера по имени (remarks). По умолчанию используется индекс |
| `-i <index>`   | Выбор сервера по индексу (по умолчанию: `0`)         |
| `-d <level>`   | Уровень детализации логов (0 - минимальный, 1 - инфо, 2 - отладка)  |
| `--proxy <URL>`| Прокси для загрузки конфигураций (например, `socks5://127.0.0.1:1080`) |

---

## 🧪 Примеры

### Выбор сервера по имени

```bash
./update-singbox.py -u https://example.com/proxy-config.json -r "FastServerEU"
```

### Выбор сервера по индексу

```bash
./update-singbox.py -u https://example.com/proxy-config.json -i 2
```

### Включение режима отладки

```bash
./update-singbox.py -u https://example.com/proxy-config.json -d 2
```

### Использование прокси для загрузки конфигурации

```bash
./update-singbox.py -u https://example.com/proxy-config.json --proxy socks5://127.0.0.1:1080
```

---

## ⏱ Планирование обновлений

Добавьте задачу в `cron` для регулярных обновлений:

```bash
crontab -e
```

**Пример для еженедельных обновлений:**

```
0 0 * * 0 /path/to/update-singbox.py -u https://example.com/proxy-config.json >> /var/log/update-singbox.log 2>&1
```

---

## 🛠 Конфигурация

- **Шаблон**: Используется `config.template.json` для создания `/etc/sing-box/config.json`.
- **Содержимое**:
  - Входящий TProxy на порту `12345`.
  - Прямая маршрутизация для российских доменов (`.ru`, `.рф`, ВКонтакте, Сбербанк и др.) и `geoip-ru`.
  - Проксирование остального трафика.

### Пути

| Назначение         | Путь                            |
| ------------------ | ------------------------------- |
| Файл конфигурации  | `/etc/sing-box/config.json`      |
| Резервная копия    | `/etc/sing-box/config.json.bak`  |
| Логи               | `/var/log/update-singbox.log`    |

### Настройка

Измените переменные в `update-singbox.py` для пользовательских путей:

```python
CONFIG_FILE = "/custom/path/to/config.json"
TEMPLATE_FILE = "/custom/path/to/template.json"
```

### Переменные окружения

| Переменная                | Описание                                      | Значение по умолчанию                      |
| ------------------------- | --------------------------------------------- | ------------------------------------------ |
| `SINGBOX_LOG_FILE`        | Путь к файлу логов                            | `/var/log/update-singbox.log`              |
| `SINGBOX_CONFIG_FILE`     | Путь к файлу конфигурации                     | `/etc/sing-box/config.json`                |
| `SINGBOX_BACKUP_FILE`     | Путь к резервной копии конфигурации           | `/etc/sing-box/config.json.bak`            |
| `SINGBOX_TEMPLATE_FILE`   | Путь к шаблону конфигурации                   | `./config.template.json`                   |
| `SINGBOX_PROXY`           | Прокси для загрузки конфигурации (опционально)| Не задан                                   |

---

## 📦 Поддерживаемые протоколы

| Протокол        | Параметры                                                  |
| --------------- | ----------------------------------------------------------- |
| **VLESS**       | UUID, flow, reality/TLS, транспорты WebSocket/gRPC/HTTP/TCP |
| **Shadowsocks** | Метод, пароль, плагин, параметры плагина                    |
| **VMess**       | UUID, безопасность                                          |
| **Trojan**      | Пароль, TLS                                                |
| **TUIC**        | UUID, пароль                                               |
| **Hysteria2**   | Пароль                                                     |

---

## 🧯 Отладка

- Логи сохраняются в `/var/log/update-singbox.log`.
- Для подробного логирования используйте флаг `-d`:
  ```bash
  ./update-singbox.py -u https://example.com/proxy-config.json -d
  ```
- Проверьте права доступа к `/etc/sing-box/` и `/var/log/`.
- Проверьте статус sing-box:
  ```bash
  systemctl status sing-box.service
  ```
- Убедитесь, что URL возвращает валидный JSON с конфигурацией серверов.
- При ошибке проверьте файл логов для получения подробностей.

---

## 🤝 Вклад в проект

Приветствуются любые улучшения! Форкните репозиторий, внесите изменения и отправьте Pull Request. Предложения по новым протоколам, оптимизациям или функциям высоко ценятся.

---

## 🙏 Благодарности

- **[momai](https://github.com/momai)** – за помощь, идеи и критическую обратную связь.
- **Команда SagerNet** – за разработку sing-box.
- **Контрибьюторы** – за предоставление конфигураций прокси и поддержку открытого интернета.

---

## 📜 Лицензия

Проект распространяется под лицензией **GNU General Public License v3.0**.  
Подробности см. в [`LICENSE`](LICENSE).

---

# update-singbox (English)

A Python script for automating configuration updates for [sing-box](https://sing-box.sagernet.org/), a universal proxy platform. This tool fetches proxy server details from a specified URL and applies them to a sing-box configuration, supporting multiple protocols and routing rules.

---

## ✨ Features

- Fetches and applies proxy server configurations from a provided URL.
- Supports protocols: **VLESS**, **Shadowsocks**, **VMess**, **Trojan**, **TUIC**, **Hysteria2**.
- Routes Russian domains (`.ru`, `.рф`, VKontakte, Yandex, etc.) and `geoip-ru` directly, proxying other traffic.
- Logs updates to `/var/log/update-singbox.log` with rotation at 1MB.
- Creates configuration backups before updates.
- Integrates with `cron` for scheduled updates.
- **Supports proxy usage** for fetching configurations via `--proxy` option.
- Log detalisation levels via `--debug`.
---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
```

### Install dependencies

- **Python 3.10 or newer** (required for `match` constructs).
- **sing-box** (follow [installation instructions](https://sing-box.sagernet.org/guide/installation/)).
- **Python requests library with SOCKS support** (`requests[socks]`).

**Example for Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3 python3-pip
pip install -r requirements.txt
```

### Copy the configuration template (optional)

```bash
sudo mkdir -p /etc/sing-box
sudo cp config.template.json /etc/sing-box/
```

### Make the script executable

```bash
chmod +x update-singbox.py
```

---

## ⚙️ Usage

Run the script with a URL providing proxy server configurations:

```bash
./update-singbox.py -u https://example.com/proxy-config.json
```

### Options

| Option         | Description                                   |
| -------------- | --------------------------------------------- |
| `-u <URL>`     | URL for proxy configuration (**required**)   |
| `-r <remarks>` | Select server by remarks (name). Defaults to index if not specified |
| `-i <index>`   | Select server by index (default: `0`)        |
| `-d <level>`   | Logging verbosity level (0 - warning, 1 - info, 2 - debug)       |
| `--proxy <URL>`| Proxy for fetching configurations (e.g., `socks5://127.0.0.1:1080`) |

---

## 🧪 Examples

### Select server by remarks

```bash
./update-singbox.py -u https://example.com/proxy-config.json -r "FastServerEU"
```

### Select server by index

```bash
./update-singbox.py -u https://example.com/proxy-config.json -i 2
```

### Enable debug mode

```bash
./update-singbox.py -u https://example.com/proxy-config.json -d 2
```

### Use a proxy for fetching configurations

```bash
./update-singbox.py -u https://example.com/proxy-config.json --proxy socks5://127.0.0.1:1080
```

---

## ⏱ Scheduling Updates

Add to `cron` for regular updates:

```bash
crontab -e
```

**Example for weekly updates:**

```
0 0 * * 0 /path/to/update-singbox.py -u https://example.com/proxy-config.json >> /var/log/update-singbox.log 2>&1
```

---

## 🛠 Configuration

- **Template**: Uses `config.template.json` to generate `/etc/sing-box/config.json`
- **Includes**:
  - TProxy inbound on port `12345`
  - Direct routing for Russian domains (`.ru`, `.рф`, VKontakte, Sberbank, etc.) and `geoip-ru`
  - Proxy routing for all other traffic

### Paths

| Purpose            | Path                            |
| ------------------ | ------------------------------- |
| Configuration file | `/etc/sing-box/config.json`      |
| Backup file        | `/etc/sing-box/config.json.bak`  |
| Logs               | `/var/log/update-singbox.log`    |

### Customization

Edit variables in `update-singbox.py` for custom paths:

```python
CONFIG_FILE = "/custom/path/to/config.json"
TEMPLATE_FILE = "/custom/path/to/template.json"
```

### Environment Variables

| Variable                | Description                                      | Default Value                             |
| ----------------------- | ------------------------------------------------ | ----------------------------------------- |
| `SINGBOX_LOG_FILE`      | Path to log file                                 | `/var/log/update-singbox.log`             |
| `SINGBOX_CONFIG_FILE`   | Path to configuration file                       | `/etc/sing-box/config.json`               |
| `SINGBOX_BACKUP_FILE`   | Path to backup configuration file                | `/etc/sing-box/config.json.bak`           |
| `SINGBOX_TEMPLATE_FILE` | Path to configuration template                   | `./config.template.json`                  |
| `SINGBOX_PROXY`         | Proxy for fetching configurations (optional)     | Not set                                   |

---

## 📦 Supported Protocols

| Protocol        | Parameters                                                  |
| --------------- | ----------------------------------------------------------- |
| **VLESS**       | UUID, flow, reality/TLS, WebSocket/gRPC/HTTP/TCP transports |
| **Shadowsocks** | Method, password, plugin, plugin_opts                      |
| **VMess**       | UUID, security                                              |
| **Trojan**      | Password, TLS                                               |
| **TUIC**        | UUID, password                                              |
| **Hysteria2**   | Password                                                    |

---

## 🧯 Troubleshooting

- Check logs: `/var/log/update-singbox.log`
- Enable detailed logging with `-d`:
  ```bash
  ./update-singbox.py -u https://example.com/proxy-config.json -d
  ```
- Ensure write permissions to `/etc/sing-box/` and `/var/log/`
- Verify sing-box status:
  ```bash
  systemctl status sing-box.service
  ```
- Confirm the URL returns valid JSON with server configurations.
- If the script fails, check the log file for detailed error information.

---

## 🤝 Contributing

Contributions are welcome! Fork the repository, make changes, and submit a Pull Request. Suggestions for new protocols, optimizations, or features are appreciated.

---

## 🙏 Acknowledgments

- **[momai](https://github.com/momai)** – for help, ideas, and critical feedback.
- **The SagerNet team** – for developing sing-box.
- **Contributors** – for sharing proxy configurations and supporting open internet access.

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.  
See [`LICENSE`](LICENSE) for details.

