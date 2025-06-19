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

## Ветка `dev`
- Все изменения разрабатываются и тестируются в ветке `dev`.
- CI автоматически запускает тесты и проверяет покрытие.

## Ветка `main`
- После принятия PR из `dev` в `main`:
  - Удаляются тесты, CI/CD конфигурации и вспомогательные файлы.
  - Генерируется changelog.
  - Создаётся релиз с автогенерацией тегов.

## Workflows
- **CI для `dev`**: `.github/workflows/ci-dev.yml`
- **Релиз для `main`**: `.github/workflows/release-main.yml` 