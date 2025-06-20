# Другие языки / Other languages
- [English (DEVELOPMENT.md)](../DEVELOPMENT.md)

# Онбординг

Добро пожаловать в процесс разработки! Если вы новый участник, выполните следующие шаги:

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/kpblcaoo/update-singbox.git
   cd update-singbox
   ```
2. **Создайте виртуальное окружение и активируйте его:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. **Установите зависимости для разработки:**
   ```bash
   pip install .[dev]
   ```
4. **Скопируйте пример файла окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env при необходимости
   ```
5. **Запустите тесты:**
   ```bash
   pytest
   ```
6. **Ознакомьтесь с разделом CONTRIBUTING в README.md для стандартов кода и процесса PR.**

---

# Процесс разработки и релиза

## Базовые ветки

| Ветка | Назначение |
|-------|------------|
| `main` | Всегда зелёная, production-ready. Теги релизов (`v1.4.0`, `v1.5.0` …). |
| `develop` | Интеграционная ветка следующей версии (сейчас 1.5.0). |
| `release/x.y.z` | Стабилизация релиза; багфиксы только сюда. После релиза сливается в `main` и `develop`. |
| `hotfix/x.y.z+1` | Критический фикс для `main`; затем cherry-pick в `develop`. |

### Фича-ветки
Создавайте короткоживущие ветки от `develop`:

```bash
git checkout develop && git pull
git checkout -b feat/C-01-pydantic-models
```

Слияние через Pull Request → squash-merge в `develop`.

## CI / CD Workflows

| Workflow | Триггер |
|----------|---------|
| `ci.yml` | Pull Request-ы и pushes в `develop` / feature ветки — линтер, тесты, покрытие |
| `release.yml` | Тегированные коммиты в `main` — сборка, публикация артефактов, PyPI, Docker | 