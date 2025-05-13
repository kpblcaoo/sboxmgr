import pytest
from unittest.mock import patch
from modules.config_fetch import fetch_json as fetch_config

@patch("modules.config_fetch.requests.get")
def test_fetch_config_valid(mock_get):
    # Подготовка mock-ответа
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"key": "value"}

    # Пример теста для проверки корректной загрузки конфигурации
    config = fetch_config("https://example.com/tests/config.json")
    assert config == {"key": "value"}

@patch("modules.config_fetch.requests.get")
def test_fetch_config_invalid(mock_get):
    # Подготовка mock-ответа с ошибкой
    mock_get.side_effect = Exception("Failed to fetch")

    # Пример теста для проверки обработки некорректного пути
    with pytest.raises(Exception):
        fetch_config("https://invalid-url.com")
