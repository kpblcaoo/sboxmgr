from unittest.mock import patch
from update_singbox import manage_service
import pytest

@patch("shutil.which", return_value="/usr/bin/systemctl")
@patch("subprocess.run")
def test_manage_service_restart(mock_run, mock_which):
    mock_run.return_value.returncode = 0
    manage_service()
    mock_run.assert_any_call(["systemctl", "is-active", "--quiet", "sing-box.service"], check=False)
    mock_run.assert_any_call(["systemctl", "restart", "sing-box.service"], check=True)

@patch("shutil.which", return_value=None)
def test_manage_service_no_systemctl(mock_which):
    with pytest.raises(SystemExit) as excinfo:
        manage_service()
    # Проверяем код выхода
    assert excinfo.value.code == 1