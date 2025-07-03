import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture(autouse=True)
def mock_get_logger():
    with patch('src.sboxmgr.logging.core.get_logger', return_value=MagicMock()):
        yield 