import pytest
from unittest.mock import patch, MagicMock
from modules.service_manage import manage_service

@patch("modules.service_manage.subprocess.run")
def test_manage_service(mock_run):
    # Пример теста для проверки управления сервисом
    mock_run.return_value = MagicMock(returncode=0)  # Замокировать успешное выполнение команды
    try:
        manage_service()
    except Exception as e:
        assert False, f"Test failed with exception: {e}"
