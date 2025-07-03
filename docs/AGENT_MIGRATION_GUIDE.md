# Руководство по миграции: Управление сервисами через агент

## Обзор

В соответствии с ADR-0015, управление сервисами было вынесено из `sboxmgr` в отдельный агент `sboxagent`. Это изменение улучшает архитектуру, разделяя ответственность между компонентами.

## Что изменилось

### Раньше (до ADR-0015)
```bash
# sboxmgr автоматически перезапускал сервис после обновления конфигурации
sboxmgr subscription orchestrated -u https://example.com/subscription
```

### Теперь (после ADR-0015)
```bash
# 1. Генерация конфигурации
sboxmgr subscription orchestrated -u https://example.com/subscription

# 2. Управление сервисом через агент
sboxmgr agent restart
```

## Разделение ответственности

| Компонент | Ответственность |
|-----------|-----------------|
| **sboxmgr** | Обработка подписок, генерация конфигураций, валидация |
| **sboxagent** | Управление сервисами, мониторинг, автообновления |
| **Инсталлер** | Установка системных зависимостей (sing-box, clash, wireguard) |

## Установка агента

### Автоматическая установка
```bash
curl -sSL https://sbox.dev/install.sh | bash
```

### Ручная установка
```bash
# Установка только агента
sboxmgr install agent

# Установка агента и backend (sing-box/clash)
sboxmgr install backend

# Полная установка
sboxmgr install full
```

## Новые команды управления агентом

### Статус и мониторинг
```bash
# Показать статус агента
sboxmgr agent status

# Показать логи агента
sboxmgr agent logs

# Показать конфигурацию агента
sboxmgr agent config show
```

### Управление сервисом
```bash
# Запустить агент
sboxmgr agent start

# Остановить агент
sboxmgr agent stop

# Перезапустить агент
sboxmgr agent restart
```

## Типичные сценарии использования

### 1. Первоначальная настройка
```bash
# Установить агент
sboxmgr install agent

# Настроить подписку
sboxmgr subscription orchestrated -u https://example.com/subscription

# Запустить агент для автоматического управления
sboxmgr agent start
```

### 2. Обновление конфигурации
```bash
# Обновить конфигурацию из подписки
sboxmgr subscription orchestrated -u https://example.com/subscription

# Перезапустить сервис для применения изменений
sboxmgr agent restart
```

### 3. Мониторинг и отладка
```bash
# Проверить статус
sboxmgr agent status

# Просмотреть логи
sboxmgr agent logs

# Проверить конфигурацию
sboxmgr agent config show
```

## Конфигурация агента

Агент использует файл `agent.yaml` для настройки:

```yaml
# agent.yaml
log_sink:
  type: "stdout"
  path: "/var/log/sboxagent.log"

health_check:
  interval: "30s"
  timeout: "10s"

runner:
  mode: "direct"
  command: ["sboxmgr", "export"]

# Настройки интеграции с sboxmgr
integration:
  config_path: "/etc/sing-box/config.json"
  backup_path: "/etc/sing-box/config.json.bak"
```

## Преимущества новой архитектуры

### 1. Безопасность
- Агент работает с минимальными правами
- Разделение ответственности снижает риски

### 2. Гибкость
- Независимое управление конфигурацией и сервисами
- Возможность настройки автообновлений

### 3. Надёжность
- Агент может восстанавливаться после сбоев
- Мониторинг состояния сервисов

### 4. Тестируемость
- sboxmgr можно тестировать без установленного sing-box
- Изолированное тестирование компонентов

## Обратная совместимость

### Что работает как раньше
- Все команды `sboxmgr subscription` для обработки подписок
- Команды `sboxmgr export` для генерации конфигураций
- Команды `sboxmgr profile` для работы с профилями

### Что изменилось
- Команды больше не перезапускают сервисы автоматически
- Добавлены новые команды `sboxmgr agent` для управления сервисами

## Устранение неполадок

### Агент не запускается
```bash
# Проверить статус
sboxmgr agent status

# Просмотреть логи
sboxmgr agent logs

# Проверить конфигурацию
sboxmgr agent config show
```

### Сервис не применяет конфигурацию
```bash
# Проверить, что конфигурация сгенерирована
ls -la /etc/sing-box/config.json

# Перезапустить агент
sboxmgr agent restart

# Проверить статус sing-box
systemctl status sing-box
```

### Проблемы с правами доступа
```bash
# Проверить права на файлы конфигурации
ls -la /etc/sing-box/

# Исправить права при необходимости
sudo chown -R sboxagent:sboxagent /etc/sing-box/
```

## Часто задаваемые вопросы

### Q: Нужно ли устанавливать агент?
A: Да, для полной функциональности (автообновления, управление сервисами) требуется агент.

### Q: Можно ли использовать sboxmgr без агента?
A: Да, sboxmgr может работать независимо для генерации конфигураций, но управление сервисами нужно будет выполнять вручную.

### Q: Как настроить автообновления?
A: Агент автоматически настраивает автообновления при установке. Настройки можно изменить в `agent.yaml`.

### Q: Что делать, если агент не работает?
A: Проверьте логи агента (`sboxmgr agent logs`) и убедитесь, что sing-box установлен и настроен.

## Дополнительные ресурсы

- [ADR-0015: Agent-Installer Separation](../docs/arch/decisions/ADR-0015-agent-installer-separation.md)
- [Справочник CLI команд](../docs/ru/cli_reference.md)
- [Руководство по использованию агента](../docs/AGENT_BRIDGE_USAGE.md)
