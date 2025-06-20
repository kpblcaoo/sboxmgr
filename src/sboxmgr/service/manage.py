import shutil
import subprocess
from logging import error, info
import os

def manage_service():
    """Restart or start sing-box service."""
    # --- TEST-ONLY CODE ---
    # Этот блок используется исключительно для тестирования CLI:
    # если установлена переменная окружения SBOXMGR_TEST_MODE,
    # все вызовы systemctl будут отключены (no-op).
    # Это необходимо, потому что monkeypatch не работает с subprocess в CLI-тестах.
    # В production-логике переменная не должна использоваться.
    # TODO: При появлении лучшей архитектуры (например, DI или mock subprocess) — удалить.
    if os.environ.get("SBOXMGR_TEST_MODE") == "1":
        print("[Info] manage_service mock: ignoring error and exiting with code 0")
        return
    if not shutil.which("systemctl"):
        error("systemctl not found; cannot manage sing-box service")
        raise EnvironmentError("systemctl not found")
    try:
        result = subprocess.run(["systemctl", "is-active", "--quiet", "sing-box.service"], check=False)
        action = "restart" if result.returncode == 0 else "start"
        subprocess.run(["systemctl", action, "sing-box.service"], check=True)
        info(f"Service {action}ed")
    except subprocess.CalledProcessError:
        error(f"Failed to {action} sing-box service")
        raise
