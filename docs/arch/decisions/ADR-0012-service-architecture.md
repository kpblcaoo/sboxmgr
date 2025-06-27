# ADR-0012: Service Architecture & Dual-Path Support

## Статус

**Дата:** 2025-06-27  
**Статус:** ✅ **ПРИНЯТО**  
**Контекст:** Stage 4 планирование - как организовать фоновую логику авто-обновления

## TL;DR

- `sboxmgr` остаётся oneshot CLI-инструментом.
- Поддерживается два пути автообновления: через systemd timer (`autoupdater`) и через Go-агент (`sboxagent`).
- Агент умеет перехватывать логи, планировать обновления, health-check и запускать `sboxmgr` в безопасном режиме.
- `autoupdater` может быть установлен вручную или через `install-autoupdater --apply`.
- Все компоненты можно использовать отдельно или вместе, приоритет: `agent > autoupdater > cron`.

## Контекст

Нужно решить архитектуру "фонового" слоя для авто-обновления конфигураций и системного контроля. Есть несколько вариантов от простого CLI до полноценного агента.

## Решение

### 1. Трехуровневая архитектура

| Компонент | Назначение | Язык | Долгоживущий | Целевая аудитория |
|-----------|------------|------|--------------|-------------------|
| **sboxmgr** | CLI для генерации конфигов | Python | ❌ (oneshot) | Dev/CI, ручное управление |
| **autoupdater** | Timer-based авто-обновление | Shell + systemd | ❌ (timer) | "Чистые" пользователи |
| **sboxagent** | Полноценный демон-агент | Go | ✅ | Power users, домашние хабы |

### 2. Dual-Path Support

Поддерживаем два пути авто-обновления с приоритетом загрузки:

**Приоритет:** `sboxagent` → `autoupdater` → `cron` (высший приоритет перекрывает низший)

**Path A: Autoupdater (минимальный)**
```
systemd.timer → updater.sh → sboxmgr generate
```

**Path B: Agent (полный)**
```
sboxagent.service → runner (direct/shell) → sboxmgr generate
```

### 3. UX Strategy

#### Wizard-based подход:
```bash
sboxmgr wizard                    # CLI-only setup
sboxmgr wizard --autoupdater      # Timer-based setup
sboxagent wizard                  # Full agent setup
```

#### Единая команда помощи:
```bash
sboxmgr help services             # Показывает оба сценария с готовыми командами
```

#### Конфигурационные файлы:
- `/etc/sboxmgr/updater.conf` - подписки + output paths
- `/etc/sboxagent/agent.yaml` - health, notify, runner choice

### 4. Файлы и пути

| Файл/директория | Назначение |
|-----------------|------------|
| `/etc/sboxmgr/updater.conf` | Подписки и выходные пути |
| `/etc/sboxagent/agent.yaml` | Конфиг агента |
| `/etc/systemd/system/sboxmgr-autoupdater.*` | Unit/timer |
| `/usr/bin/sboxmgr` | CLI |
| `/usr/bin/sboxagent` | Агент (если установлен) |
| `/var/log/sboxagent.log` | (если log_sink=file) |

### 5. Инсталляция

#### Режим B (по умолчанию): Template generation
```bash
sboxmgr svc-template > sboxmgr-autoupdater.timer
sboxmgr svc-template > sboxmgr-autoupdater.service
```

#### Режим C (опционально): Direct installation
```bash
sboxmgr install-autoupdater --apply --enable
sboxmgr install-autoupdater --apply --user    # Rootless: ~/.config/systemd/user/
```
- Проверка root прав (кроме --user)
- Подтверждение действий
- Автоматический daemon-reload

**Note:** .deb/.rpm пакеты - future work. Сейчас только manual installation и install scripts.

### 6. Agent Runner Strategy

Гибридный подход в `sboxagent`:
```yaml
# agent.yaml
runner:
  mode: "direct"  # или "shell" (не type для избежания конфликтов)
  shell_script: "/etc/sboxmgr/updater.sh"  # если mode: shell
```

### 7. Logging Consolidation

**Централизация логирования через агент:**

#### Архитектура:
```
sboxmgr --log-format=json → stdout → sboxagent → единый лог
```

#### Реализация:
```bash
# В sboxagent
cmd := exec.Command("sboxmgr", "generate", "--log-format=json")
stdout, _ := cmd.StdoutPipe()
# Парсим JSON log-entries → log.Info(), log.Warn()
```

#### Конфигурация:
```yaml
# agent.yaml
log_sink:
  type: "stdout"  # или file, journald, telemetry
  path: "/var/log/sboxagent.log"
```

#### Fallback:
- При `--no-agent` sboxmgr логирует сам
- При сбое агента - fallback на встроенное логирование

## Последствия

### Положительные:
- ✅ Покрывает все сегменты пользователей
- ✅ Минимальный риск (fallback path)
- ✅ Четкое разделение ответственности
- ✅ Легко паковать в .deb/.rpm
- ✅ Единый лог через агент (без дублирования)
- ✅ Rootless сценарии (--user flag)

### Отрицательные:
- ❌ Поддержка двух путей (документация, тесты)
- ❌ Два конфигурационных файла
- ❌ Go-бинарник требует доверия
- ❌ Сложность UX для новичков

### Риски:
- 🔴 Потенциальная путаница в конфигурации
- 🔴 Авто-дедупликация: если обнаружен активный timer при запуске агента
- ⚠️ Пользователь может включить и timer, и agent, не зная об этом → sboxagent при старте должен предупреждать, если autoupdater.timer активен.

## Альтернативы

### A. Только CLI
- ❌ Нет авто-обновлений
- ❌ Плохой UX для большинства пользователей

### B. Только Agent
- ❌ Слишком сложно для простых случаев
- ❌ Go-зависимость для всех

### C. Монолитный Python daemon
- ❌ Смешивание build-time и run-time логики
- ❌ Сложность с systemd integration

## Реализация

### Phase 1: Foundation
- [ ] `sboxmgr svc-template` command
- [ ] `sboxmgr install-autoupdater` command (--user support)
- [ ] Basic systemd unit/timer templates
- [ ] `updater.sh` в репозитории
- [ ] Wizard commands для всех путей

### Phase 2: Agent Skeleton
- [ ] Go agent with cobra CLI
- [ ] Runner abstraction (mode: direct/shell)
- [ ] Basic health check
- [ ] Auto-de duplication detection

### Phase 3: Integration
- [ ] Configuration file management
- [ ] Legal disclaimer integration
- [ ] `sboxmgr help services` command
- [ ] Logging consolidation (--log-format=json)

### Phase 4: Testing
- [ ] E2E tests for all paths
- [ ] Integration tests with systemd
- [ ] Performance benchmarks
- [ ] Rootless scenarios testing

## Связанные ADR

- ADR-0001: CLI Security Model
- ADR-0010: Logging Core
- ADR-0011: Event System

---

**Автор:** Architecture Team  
**Рецензенты:** Security Team, UX Team 