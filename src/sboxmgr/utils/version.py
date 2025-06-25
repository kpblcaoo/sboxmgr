"""
Sing-box version checking and compatibility utilities.

DEPRECATED: Version detection relies on executing the external ``sing-box
version`` command which is considered an **external dependency**.  As of
v1.5.0 the default CLI behaviour is to **skip** version compatibility checks
(see ``--skip-version-check`` flag) and delegate this responsibility to the
up-coming *sboxagent* component.  This module will be removed once agent-based
validation is fully integrated.
"""
import subprocess
import re
from typing import Optional, Tuple
from packaging import version


def get_singbox_version() -> Optional[str]:
    """
    Получает версию установленного sing-box.
    
    Returns:
        str: Версия sing-box (например, "1.10.5") или None если не удалось определить
    """
    try:
        result = subprocess.run(
            ["sing-box", "version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            # Ищем версию в выводе (формат: "sing-box version 1.10.5")
            match = re.search(r'sing-box version (\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
            
            # Альтернативный формат (только номер версии)
            match = re.search(r'(\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
                
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass
    
    return None


def check_version_compatibility(required_version: str = "1.11.0") -> Tuple[bool, Optional[str], str]:
    """
    Проверяет совместимость версии sing-box с требуемой минимальной версией.
    
    Args:
        required_version: Минимальная требуемая версия (по умолчанию 1.11.0)
        
    Returns:
        Tuple[bool, Optional[str], str]: (совместима, текущая_версия, сообщение)
    """
    current_version = get_singbox_version()
    
    if current_version is None:
        return False, None, "Не удалось определить версию sing-box. Убедитесь, что sing-box установлен и доступен в PATH."
    
    try:
        current = version.parse(current_version)
        required = version.parse(required_version)
        
        if current >= required:
            return True, current_version, f"Версия sing-box {current_version} совместима (требуется >= {required_version})"
        else:
            return False, current_version, f"Версия sing-box {current_version} устарела. Требуется >= {required_version} для полной поддержки современного синтаксиса."
            
    except Exception as e:
        return False, current_version, f"Ошибка при сравнении версий: {e}"


def should_use_legacy_outbounds(singbox_version: Optional[str] = None) -> bool:
    """
    Определяет, нужно ли использовать legacy special outbounds для совместимости.
    
    Args:
        singbox_version: Версия sing-box (если не указана, определяется автоматически)
        
    Returns:
        bool: True если нужно использовать legacy outbounds (версия < 1.11.0)
    """
    if singbox_version is None:
        singbox_version = get_singbox_version()
    
    if singbox_version is None:
        # Если версию определить нельзя, используем современный синтаксис
        return False
    
    try:
        current = version.parse(singbox_version)
        legacy_threshold = version.parse("1.11.0")
        return current < legacy_threshold
    except Exception:
        # При ошибке парсинга используем современный синтаксис
        return False


def get_version_warning_message(current_version: str) -> str:
    """
    Генерирует предупреждающее сообщение для устаревших версий.
    
    Args:
        current_version: Текущая версия sing-box
        
    Returns:
        str: Текст предупреждения
    """
    return f"""
⚠️  ПРЕДУПРЕЖДЕНИЕ: Обнаружена устаревшая версия sing-box {current_version}

Рекомендуется обновление до версии 1.11.0 или выше для:
- Поддержки современного синтаксиса rule actions
- Устранения deprecated warnings
- Улучшенной производительности и безопасности

Для обновления sing-box посетите: https://sing-box.sagernet.org/installation/
""" 