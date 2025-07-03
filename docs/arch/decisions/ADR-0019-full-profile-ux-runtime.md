# ADR-0019: Full Profile UX & Runtime Management

## Статус

**Дата:** 2025-06-29  
**Статус:** ✅ **ПРИНЯТО**  
**Контекст:** Production-ready UX и runtime-аспекты для профилей и подписок

---

## TL;DR

- Вводится модель `active_profile` и команды переключения
- Специфицируются политики автопереключения профилей
- Вводится хранилище профилей, история активаций и profile.lock
- Реализуется полноценный CLI-UX для управления подписками
- Вводятся snapshot/e2e тесты на профили и обратную совместимость
- Создаётся документация и команда миграции

---

## 1. Переключение между профилями (ActiveProfile)

- Ввести поле `active_profile` в `integration.yaml` и поддерживать через ENV (`SBOX_ACTIVE_PROFILE`)
- CLI-команда `sboxmgr profile switch <id>` меняет active_profile
- Агент читает active_profile из integration.yaml или ENV
- Реализовать модуль ProfileStateManager

---

## 2. Политики автопереключения профилей

- Добавить секцию `switch_policy` в profile.json или agent.yaml
- Формат: условие, fallback, действия
- Реализовать PolicyEngine для runtime-переключения

---

## 3. Хранилище профилей и история

- Каталог профилей: `~/.config/sboxmgr/profiles/`
- Журнал активаций: `.profile-history.jsonl`
- Лок-файл: `profile.lock` с hash последнего профиля
- Реализовать ProfileHistoryManager

---

## 4. CLI UX и изоляция подписок

- Команды:
  - `sboxmgr subscription add/remove/list/enable/disable/preview`
  - Флаги: `--only-subscription id`, `--exclude-subscription id`
- UX: быстрое добавление, временное отключение, просмотр состояния

---

## 5. Тесты и обратная совместимость

- Ввести e2e/snapshot тесты:
  - `profile.json → ParsedServerList → config.json`
  - Сравнение с legacy-конфигом
- Проверять apply с профилем и без

---

## 6. Документация и миграция

- Страница: `docs/ru/full_profiles.md` с примерами, таблицей совместимости, миграцией
- Команда: `sboxmgr migrate-to-profile`

---

## План внедрения (Phase 5/6)

1. Реализация ProfileStateManager и active_profile
2. PolicyEngine для автопереключения
3. ProfileHistoryManager и файловая структура
4. CLI-UX для подписок (add/remove/list/preview)
5. E2E/snapshot тесты на профили
6. Документация и миграция

---

## Связанные ADR

- ADR-0017: Full Profile Architecture
- ADR-0018: Subscription Management Architecture
- ADR-0016: Pydantic Schema Generation
- ADR-0015: Agent-Installer Separation
- ADR-0012: Service Architecture 