# Sboxmgr CLI Showcase

A quick demonstration of the most useful CLI scenarios for sboxmgr (`sboxctl`).

---

## 🎯 What you can do
- Select and apply proxy servers from a remote config
- Exclude servers from selection (and manage exclusions)
- Preview config changes without writing files (dry-run)
- List all available servers with details
- Manage everything via a modern, scriptable CLI

---

## 🚀 1. Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
cp .env.example .env  # Edit as needed
sboxctl run -u https://example.com/proxy-config.json --index 1
```

---

## 🏁 2. Typical CLI scenarios

### Select and apply a server by index
```bash
sboxctl run -u https://example.com/proxy-config.json --index 1
# Output: config.json generated for the selected server
```

### Preview config (dry-run, no file changes)
```bash
sboxctl dry-run -u https://example.com/proxy-config.json
# Output: config printed to stdout, no files written
```

### List all available servers
```bash
sboxctl list-servers -u https://example.com/proxy-config.json
# Output: Table of servers with indices, remarks, protocols, etc.
```

### Exclude a server by index
```bash
sboxctl exclusions -u https://example.com/proxy-config.json --add 2
# Output: Server with index 2 added to exclusions.json
```

### Remove a server from exclusions
```bash
sboxctl exclusions -u https://example.com/proxy-config.json --remove 2
# Output: Server with index 2 removed from exclusions.json
```

### View current exclusions
```bash
sboxctl exclusions --view
# Output: List of currently excluded servers
```

### Clear all exclusions
```bash
sboxctl clear-exclusions
# Output: exclusions.json emptied
```

---

## ⚠️ 3. Error handling examples

### Invalid or empty URL
```bash
sboxctl run -u ""
# Output: Error: URL is required (exit code 1)
```

### Trying to select a non-existent server
```bash
sboxctl run -u https://example.com/proxy-config.json --index 99
# Output: Error: No server with index 99 found (exit code 1)
```

---

## 🛠️ 4. Best practices & tips
- Use `.env.example` to configure all paths, URLs, and debug levels.
- For scripting, check exit codes: `0` = success, `1` = error.
- Use `--dry-run` to preview changes before applying.
- All CLI commands support `--help` for usage info.
- **If you can't remove an exclusion by index or ID, use `sboxctl clear-exclusions --yes` to fully clear exclusions, or manually edit `exclusions.json`. This is a temporary workaround until UX is improved.**
- For advanced usage and development, see [README.md](./README.md) and [DEVELOPMENT.md](./docs/DEVELOPMENT.md).

---

## 📎 Links
- [README.md](./README.md) — full documentation
- [.env.example](./.env.example) — all environment variables
- [CHANGELOG.md](./docs/CHANGELOG.md) — latest changes

---

> Want a visual demo? Suggest a GIF or video in the issues! 