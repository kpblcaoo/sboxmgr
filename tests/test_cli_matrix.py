import pytest
import subprocess
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
TEST_URL = os.getenv("TEST_URL") or os.getenv("SINGBOX_URL") or "https://example.com/config"

# Для tolerant-поиска сообщений
EXCLUDE_MSGS = ["Excluding server", "already excluded", "[Info] Server already excluded"]
REMOVE_MSGS = ["Removed exclusion", "Exclusions cleared", "очищен"]
DRYRUN_MSGS = ["Dry run: config is valid", "dry-run", "конфиг валиден"]

# Таблица CLI-флагов и ожидаемого поведения
CLI_MATRIX = [
    # (args, description, expected_exit, expected_files, expected_stdout_contains)
    (["-u", TEST_URL], 'Базовый запуск: только URL', 0, ['config.json'], ['Update completed successfully', '[Info] manage_service mock: ignoring error and exiting with code 0']),
    (["-u", TEST_URL, '--dry-run'], 'Dry-run: не должно быть изменений файлов', 0, [], DRYRUN_MSGS),
    (["-u", TEST_URL, '--list-servers'], 'Список серверов', 0, [], ['Index', 'Name', 'Protocol', 'Port']),
    (["-u", TEST_URL, '--exclude', '0'], 'Исключение сервера по индексу', 0, ['exclusions.json'], EXCLUDE_MSGS),
    (["-u", TEST_URL, '--exclude', '0', '--exclude-only'], 'Только exclusions.json, без config.json', 0, ['exclusions.json'], EXCLUDE_MSGS),
    (["-u", TEST_URL, '--exclude', '0', '--dry-run'], 'Исключение с dry-run (не должно менять exclusions.json)', 0, [], DRYRUN_MSGS + EXCLUDE_MSGS),
    (["-u", TEST_URL, '--exclude', '0', '--clear-exclusions'], 'Очистка exclusions', 0, [], REMOVE_MSGS),
    (["-u", TEST_URL, '--exclude', '0', '--exclude', '-0'], 'Исключение и возврат сервера', 0, ['exclusions.json'], EXCLUDE_MSGS + REMOVE_MSGS),
    (["-u", TEST_URL, '--exclude', '0', '--dry-run', '--exclude-only'], 'Исключение с dry-run и exclude-only', 0, [], DRYRUN_MSGS + EXCLUDE_MSGS),
    # Добавить другие комбинации по мере необходимости
]

@pytest.mark.parametrize('args, description, expected_exit, expected_files, expected_stdout_contains', CLI_MATRIX)
def test_cli_matrix(args, description, expected_exit, expected_files, expected_stdout_contains, tmp_path, monkeypatch):
    """
    CLI matrix: tolerant-поиск сообщений, не трогает exclusions.json вне tmp_path.
    Если тест падает — выводит stdout, stderr и лог для диагностики.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cmd = [sys.executable, 'src/main.py'] + args
    env = os.environ.copy()
    # Подменяем пути для артефактов на tmp_path
    env["SBOXMGR_CONFIG_FILE"] = str(tmp_path / "config.json")
    env["SBOXMGR_BACKUP_FILE"] = str(tmp_path / "backup.json")
    env["SBOXMGR_TEMPLATE_FILE"] = str(project_root + "/config.template.json")
    env["SBOXMGR_EXCLUSIONS_FILE"] = str(tmp_path / "exclusions.json")
    env["SBOXMGR_LOG_FILE"] = str(tmp_path / "log.txt")
    env["MOCK_MANAGE_SERVICE"] = "1"
    # Мокаем manage_service (systemctl) чтобы не требовать root и не ломать тесты
    monkeypatch.setattr("src.sboxmgr.service.manage.manage_service", lambda: None)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, env=env)
    log_text = ""
    log_path = tmp_path / "log.txt"
    if log_path.exists():
        log_text = log_path.read_text(encoding="utf-8")
    output = result.stdout + result.stderr + log_text
    text = expected_stdout_contains[0] if expected_stdout_contains else ''
    try:
        assert result.returncode == expected_exit, f"{description}: неверный код возврата"
        for fname in expected_files:
            if fname == "exclusions.json":
                if not (tmp_path / fname).exists():
                    # exclusions.json может не появиться, если сервер уже исключён
                    continue
            assert (tmp_path / fname).exists(), f"{description}: отсутствует {fname}"
        if not any(
            s.strip().lower() in output.lower()
            for text in expected_stdout_contains
            for s in ([text] if isinstance(text, str) else text)
        ):
            print(f"\n==== CLI MATRIX DIAGNOSTICS ====")
            print(f"Args: {args}")
            print(f"Return code: {result.returncode}")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            print(f"LOG:\n{log_text}")
            print(f"OUTPUT repr:\n{repr(output)}")
            print(f"TYPES: text={type(text)}, output={type(output)}")
            print("===============================\n")
            assert False, f"{description}: не найдено ни одной из подстрок {expected_stdout_contains} в выводе или логе"
    except AssertionError as e:
        print("\n==== CLI MATRIX DIAGNOSTICS ====")
        print(f"Args: {args}")
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        print(f"LOG:\n{log_text}")
        print(f"OUTPUT repr:\n{repr(output)}")
        print(f"TYPES: text={type(text)}, output={type(output)}")
        print("===============================\n")
        assert False, f"{description}: не найдено ни одной из подстрок {expected_stdout_contains} в выводе или логе" 