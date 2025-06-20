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
