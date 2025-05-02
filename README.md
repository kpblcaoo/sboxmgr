
# update-singbox

A Python script for automating configuration updates for [sing-box](https://sing-box.sagernet.org/), a universal proxy platform. This tool fetches proxy server details from a specified URL and applies them to a sing-box configuration, supporting multiple protocols and routing rules.

---

## ✨ Features

- Fetches and applies proxy server configurations from a provided URL.
- Supports protocols: **VLESS**, **Shadowsocks**, **VMess**, **Trojan**, **TUIC**, **Hysteria2**.
- Routes Russian domains (`.ru`, `.рф`, VKontakte, Yandex, etc.) and `geoip-ru` directly, proxying other traffic.
- Logs updates to `/var/log/update-singbox.log` with rotation at 1MB.
- Creates configuration backups before updates.
- Integrates with `cron` for scheduled updates.

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/kpblcaoo/update-singbox.git
cd update-singbox
```

### Install dependencies

- **Python 3** (typically pre-installed on Linux)
- **sing-box** (follow [installation instructions](https://sing-box.sagernet.org/guide/installation/))

**Example for Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install python3
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
| `-d`           | Enable debug mode for detailed logging       |

---

## 🧪 Examples

Select server by remarks:

```bash
./update-singbox.py -u https://example.com/proxy-config.json -r "FastServerEU"
```

Select server by index:

```bash
./update-singbox.py -u https://example.com/proxy-config.json -i 2
```

Enable debug mode:

```bash
./update-singbox.py -u https://example.com/proxy-config.json -d
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
- Ensure write permissions to `/etc/sing-box/` and `/var/log/`
- Verify sing-box status:

```bash
systemctl status sing-box.service
```

- Confirm the URL returns valid JSON with server configurations.

---

## 🤝 Contributing

Contributions are welcome! Fork the repository, make changes, and submit a Pull Request. Suggestions for new protocols, optimizations, or features are appreciated.

---

## 🙏 Acknowledgments

- **[momai](https://github.com/momai)** – for help, ideas, and critical feedback
- **The SagerNet team** – for developing sing-box
- **Contributors** – for sharing proxy configurations and supporting open internet access

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.  
See [`LICENSE`](LICENSE) for details.
