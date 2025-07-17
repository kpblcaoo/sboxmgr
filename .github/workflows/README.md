# GitHub Actions Workflows

Этот репозиторий использует GitHub Actions для автоматизации CI/CD процессов.

## Workflows

### 1. Code Quality Check (`quality-check.yml`)

**Триггеры:**
- Push в `main` и `develop` ветки
- Pull requests в `main` и `develop` ветки
- Ручной запуск

**Проверки:**
- **Ruff**: Линтер и форматтер Python кода
- **isort**: Сортировка импортов
- **Black**: Форматирование кода
- **MyPy**: Проверка типов
- **pydocstyle**: Проверка документации
- **Bandit**: Сканирование безопасности
- **Sphinx**: Сборка документации (если есть)

### 2. Release Pipeline (`release.yml`)

**Триггеры:**
- Push тегов с префиксом `v*` (например, `v1.0.0`)
- Ручной запуск с указанием версии

**Этапы:**

#### Release Quality Checks
- Тестирование на Python 3.9, 3.10, 3.11, 3.12
- Установка пакета в development режиме
- Проверка CLI: `sboxctl --help`, `sboxctl --version`
- Запуск тестов с покрытием
- Сборка wheel и source distribution
- Проверка целостности wheel через `.hooks/check_build_contents.py`
- Валидация пакета через `twine check`
- Тестирование установки wheel в изолированном окружении
- Загрузка отчетов о покрытии в Codecov

#### Security Scan
- **Bandit**: Сканирование кода на уязвимости
- **Safety**: Проверка зависимостей на известные уязвимости
- Загрузка отчетов безопасности как артефакты

#### Publish (только для тегов)
- Публикация в PyPI
- Создание GitHub Release с автоматическими release notes
- Прикрепление собранных файлов к release

## Использование

### Автоматический Release

1. Создайте и запушьте тег:
```bash
# Для стабильного релиза
git tag v1.0.0
git push origin v1.0.0

# Для pre-release (TestPyPI)
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```

2. Workflow автоматически запустится и выполнит все проверки
3. Pre-release версии (dev, rc, alpha, beta) публикуются в TestPyPI
4. Стабильные версии публикуются в PyPI

### Ручной Release

1. Перейдите в GitHub → Actions → Release Pipeline
2. Нажмите "Run workflow"
3. Введите версию (например, `1.0.0`)
4. Нажмите "Run workflow"

### Настройка Secrets

Для публикации необходимо настроить:

1. **PYPI_API_TOKEN**: API токен PyPI (для стабильных релизов)
   - Создайте токен на https://pypi.org/manage/account/token/
   - Добавьте в GitHub Secrets

2. **TESTPYPI_API_TOKEN**: API токен TestPyPI (для pre-release)
   - Создайте токен на https://test.pypi.org/manage/account/token/
   - Добавьте в GitHub Secrets

3. **GITHUB_TOKEN**: Автоматически предоставляется GitHub

## Мониторинг

### Артефакты
- Отчеты о безопасности загружаются как артефакты
- Отчеты о покрытии отправляются в Codecov

### Уведомления
- Успешные/неуспешные сборки отправляются в GitHub
- Можно настроить интеграцию с Slack/Discord

## Локальная проверка

Перед push рекомендуется запустить проверки локально:

```bash
# Установка pre-commit
pip install pre-commit
pre-commit install

# Запуск всех проверок
pre-commit run --all-files

# Проверка wheel
python .hooks/check_build_contents.py

# Тесты
pytest --cov=sboxmgr

# Сборка
python -m build

# Проверка twine
twine check dist/*
```

## Troubleshooting

### Частые проблемы

1. **Wheel integrity check failed**
   - Проверьте, что все модули включены в `pyproject.toml`
   - Убедитесь, что `.gitignore` не исключает нужные файлы

2. **Import errors in wheel test**
   - Проверьте список `REQUIRED_IMPORTS` в `.hooks/check_build_contents.py`
   - Убедитесь, что все зависимости указаны в `pyproject.toml`

3. **Twine validation failed**
   - Проверьте метаданные в `pyproject.toml`
   - Убедитесь, что все файлы присутствуют в `dist/`

### Логи

Все логи доступны в GitHub Actions:
- GitHub → Actions → [Workflow] → [Job] → [Step]
- Можно скачать артефакты для детального анализа
