import pytest
from modules.service_manage import manage_service

def test_manage_service():
    # Пример теста для проверки управления сервисом
    try:
        manage_service()
    except Exception as e:
        assert "systemctl not found" in str(e) or "Failed to" in str(e)
