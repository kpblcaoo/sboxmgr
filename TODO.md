# TODO / Known bugs & UX issues

- [ ] Server indices in `list-servers` may start from a non-zero value. Re-index output from 0 for user clarity.
- [ ] Removing exclusions by index or ID may not work as expected. Use `sboxctl clear-exclusions --yes` or edit `exclusions.json` as a workaround. Make UX transparent, support both index and ID, always show a message.

// ... existing TODOs ...

- [ ] Интегрировать флаг --use-selected в инсталлер:
      - Инсталлер должен вызывать sboxctl run --use-selected для применения выбранных серверов из selected_config.json.
      - Добавить поддержку переменной окружения SBOXCTL_USE_SELECTED (если установлена в 1/true — эквивалентно флагу --use-selected).
      - Обновить документацию (README, SHOWCASE, примеры) с описанием флага и сценариев использования для автоматизации и CI.
      - Проверить, что обычный run всегда работает в авто-режиме (без selected_config.json, если не указан флаг/переменная).
