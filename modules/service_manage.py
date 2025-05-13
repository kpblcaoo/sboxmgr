import shutil
import subprocess
from logging import error, info

def manage_service():
    """Restart or start sing-box service."""
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
