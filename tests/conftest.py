# Инициализируем логирование для тестов ПЕРЕД всеми импортами
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Добавляем src в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sboxmgr.logging.core
from sboxmgr.config.models import LoggingConfig

# Импорты sboxmgr
from sboxmgr.logging.core import initialize_logging
from sboxmgr.subscription.models import ParsedServer, PipelineContext, PipelineResult

# Мокаем get_logger до инициализации логирования
sboxmgr.logging.core.get_logger = MagicMock(return_value=MagicMock())

# Инициализируем логирование сразу
logging_config = LoggingConfig(level="DEBUG", sinks=["stdout"], format="text")
initialize_logging(logging_config)

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class MockResponse:
    def __init__(self, content=b"dummy", status_code=200):
        self.content = content
        self.status_code = status_code
        self.raw = type('MockRaw', (), {'read': lambda self, *args, **kwargs: content})()
        self.text = content.decode('utf-8') if isinstance(content, bytes) else str(content)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
        return self

@pytest.fixture(autouse=True)
def mock_requests_get(monkeypatch):
    def mock_get(url, **kwargs):
        # Return mock subscription data for test URLs
        if "mock-subscription.example.com" in url or "example.com" in url:
            # Mock base64 encoded subscription data
            mock_data = "dm1lc3M6Ly9leGFtcGxlLXV1aWQxQGV4YW1wbGUuY29tOjQ0MyNFeGFtcGxlIFZNZXNz"
            return MockResponse(content=mock_data.encode('utf-8'), status_code=200)
        return MockResponse()
    monkeypatch.setattr("requests.get", mock_get)


def run_cli(args, env=None, cwd=None):
    """Вспомогательная функция для вызова CLI с capture_output.
    exclusions.json и selected_config.json будут создаваться в cwd (tmp_path) через env.
    """
    if env is None:
        env = os.environ.copy()
    # Указать файлы в tmp_path
    cwd = cwd or os.getcwd()
    env["SBOXMGR_EXCLUSION_FILE"] = str(Path(cwd) / "exclusions.json")
    env["SBOXMGR_SELECTED_CONFIG_FILE"] = str(Path(cwd) / "selected_config.json")
    # Использовать временный лог файл для тестов
    env["SBOXMGR_LOG_FILE"] = str(Path(cwd) / "test.log")
    result = subprocess.run(
        [sys.executable, "src/sboxmgr/cli/main.py"] + args,
        capture_output=True,
        text=True,
        env=env,
        cwd=PROJECT_ROOT,
    )
    return result


@pytest.fixture(autouse=True)
def cleanup_files(tmp_path, monkeypatch):
    """Фикстура: каждый тест работает в своём tmp_path, файлы очищаются автоматически."""
    monkeypatch.chdir(tmp_path)

    # Список файлов для очистки
    cleanup_files = [
        "exclusions.json",
        "selected_config.json",
        "config.json",
        "test_config.json",
        "test.log",
    ]

    # Очистка до теста
    for fname in cleanup_files:
        if os.path.exists(fname):
            os.remove(fname)

    yield

    # Очистка после теста
    for fname in cleanup_files:
        if os.path.exists(fname):
            os.remove(fname)


@pytest.fixture(autouse=True)
def mock_logging_setup():
    """Mock sboxmgr logging setup to prevent initialization errors during test collection."""
    with patch("sboxmgr.logging.core.initialize_logging") as mock_init, patch(
        "sboxmgr.logging.core.get_logger"
    ) as mock_get_logger:
        mock_init.return_value = None
        mock_get_logger.return_value = MagicMock()
        yield


@pytest.fixture(autouse=True)
def cleanup_project_root():
    """Очистка файлов в корне проекта после каждого теста."""
    # Список файлов для очистки в корне проекта
    root_cleanup_files = [
        "config.json",
        "test_config.json",
        "exclusions.json",
        "selected_config.json",
        "backup.json",
        "test.log",
    ]

    yield

    # Очистка после теста
    for fname in root_cleanup_files:
        file_path = PROJECT_ROOT / fname
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"Cleaned up: {file_path}")
            except Exception as e:
                print(f"Failed to clean up {file_path}: {e}")


@pytest.fixture
def test_subscription_url():
    """Get test subscription URL from environment or use mock data.

    Returns:
        str: Real subscription URL if TEST_URL is set, otherwise mock URL.
    """
    url = os.getenv("TEST_URL")
    if url and not os.getenv("SKIP_EXTERNAL_TESTS"):
        return url
    else:
        # Return a URL that will be handled by the mock_requests_get fixture
        return "https://mock-subscription.example.com/test"


@pytest.fixture
def real_subscription_available():
    """Check if real subscription URL is available for testing.

    Returns:
        bool: True if TEST_URL is set and external tests are enabled.
    """
    return bool(os.getenv("TEST_URL") and not os.getenv("SKIP_EXTERNAL_TESTS"))


@pytest.fixture
def sample_parsed_servers():
    """Provide sample parsed server objects for unit testing.

    Returns:
        list: List of ParsedServer objects with realistic test data.
    """
    return [
        ParsedServer(
            protocol="vmess",
            address="1.1.1.1",
            port=443,
            uuid="test-uuid-1",
            security="tls",
            name="Test VMess Server 1",
        ),
        ParsedServer(
            protocol="vless",
            address="2.2.2.2",
            port=443,
            uuid="test-uuid-2",
            security="tls",
            name="Test VLESS Server 1",
        ),
        ParsedServer(
            protocol="trojan",
            address="3.3.3.3",
            port=443,
            password="test-password",  # pragma: allowlist secret
            name="Test Trojan Server 1",
        ),
    ]


@pytest.fixture
def mock_pipeline_result_success(sample_parsed_servers):
    """Create a mock successful pipeline result.

    Args:
        sample_parsed_servers: Fixture providing sample server data.

    Returns:
        PipelineResult: Mock successful result with sample servers.
    """
    return PipelineResult(
        config=sample_parsed_servers,
        context=PipelineContext(mode="test"),
        errors=[],
        success=True,
    )


@pytest.fixture
def mock_pipeline_result_failure():
    """Create a mock failed pipeline result.

    Returns:
        PipelineResult: Mock failed result.
    """
    return PipelineResult(
        config=None,
        context=PipelineContext(mode="test"),
        errors=["Mock error for testing"],
        success=False,
    )


@pytest.fixture
def skip_external_tests():
    """Skip tests that require external resources.

    This fixture can be used to conditionally skip tests that require
    external subscription URLs or other external dependencies.
    """
    if os.getenv("SKIP_EXTERNAL_TESTS"):
        pytest.skip("External tests disabled")


@pytest.fixture
def require_external_tests():
    """Require external tests to be enabled.

    This fixture will skip the test if external tests are disabled
    or if TEST_URL is not set.
    """
    if not os.getenv("TEST_URL"):
        pytest.skip("TEST_URL not set")
    if os.getenv("SKIP_EXTERNAL_TESTS"):
        pytest.skip("External tests disabled")
