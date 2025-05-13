import pytest
from unittest.mock import patch
from modules.config_generate import generate_config

@patch("modules.config_generate.subprocess.run")
def test_generate_config(mock_run):
    # Подготовка mock для subprocess.run
    mock_run.return_value.returncode = 0

    # Пример теста для проверки генерации конфигурации
    outbound = {"type": "example", "key": "value"}
    template_file = "template.json"
    config_file = "tests/config.json"
    backup_file = "backup.json"
    with open(template_file, "w") as f:
        f.write("$outbound_json")
    generate_config(outbound, template_file, config_file, backup_file)
    with open(config_file, "r") as f:
        assert f.read() == "{\n  \"type\": \"example\",\n  \"key\": \"value\"\n}"
