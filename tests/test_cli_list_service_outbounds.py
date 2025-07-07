from typer.testing import CliRunner

from sboxmgr.cli.main import app


def test_list_servers_filters_service_outbounds(monkeypatch):
    """Тестирует, что команда list-servers фильтрует служебные outbounds."""
    runner = CliRunner()

    # Мокаем SubscriptionManager.export_config в модуле subscription
    def mock_export_config(*args, **kwargs):
        from sboxmgr.subscription.models import PipelineContext, PipelineResult

        return PipelineResult(
            config={
                "outbounds": [
                    # Реальные серверы
                    {
                        "type": "shadowsocks",
                        "tag": "ss-server",
                        "server": "127.0.0.1",
                        "server_port": 80,
                    },
                    {
                        "type": "vmess",
                        "tag": "vmess-server",
                        "server": "example.com",
                        "server_port": 443,
                    },
                    # Служебные outbounds (должны быть отфильтрованы)
                    {"type": "direct", "tag": "direct"},
                    {"type": "block", "tag": "block"},
                    {"type": "dns", "tag": "dns-out"},
                ]
            },
            context=PipelineContext(mode="test"),
            errors=[],
            success=True,
        )

    monkeypatch.setattr(
        "sboxmgr.subscription.manager.SubscriptionManager.export_config",
        mock_export_config,
    )

    # Также мокаем load_exclusions чтобы избежать ошибок
    def mock_load_exclusions(*args, **kwargs):
        return {"version": 1, "exclusions": []}

    monkeypatch.setattr(
        "sboxmgr.server.exclusions.load_exclusions", mock_load_exclusions
    )

    # Используем фиктивный URL (никаких реальных подписок)
    result = runner.invoke(
        app, ["list-servers", "-u", "http://example.com/fake-sub", "-d", "0"]
    )

    # Проверяем результат
    assert (
        result.exit_code == 0
    ), f"Command failed with output: {result.stdout}\nError: {result.stderr}"
    output = result.stdout

    # Должны быть только реальные серверы
    assert "ss-server" in output
    assert "vmess-server" in output

    # Служебные outbounds не должны быть в выводе
    assert "direct" not in output
    assert "block" not in output
    assert "dns-out" not in output

    # Проверяем количество серверов (должно быть 2)
    lines = [line for line in output.split("\n") if line.strip().startswith("[")]
    assert len(lines) == 2, f"Ожидалось 2 сервера, найдено {len(lines)}"
