from abc import ABC, abstractmethod
from typing import Any, Dict, List
from sboxmgr.subscription.models import PipelineContext

class ValidationResult:
    def __init__(self, valid: bool, errors: List[str] = None):
        self.valid = valid
        self.errors = errors or []

RAW_VALIDATOR_REGISTRY = {}

def register_raw_validator(name):
    def decorator(cls):
        RAW_VALIDATOR_REGISTRY[name] = cls
        return cls
    return decorator

class BaseRawValidator(ABC):
    """BaseRawValidator: абстрактный класс для raw validator-плагинов.
    plugin_type = "validator" для автодокументации и фильтрации.
    """
    plugin_type = "validator"
    @abstractmethod
    def validate(self, raw: bytes, context: PipelineContext) -> ValidationResult:
        pass

@register_raw_validator("noop")
class NoOpRawValidator(BaseRawValidator):
    def validate(self, raw: bytes, context: PipelineContext) -> ValidationResult:
        return ValidationResult(valid=True)

# DX: Базовый класс для валидаторов (для генератора шаблонов)
class BaseValidator(ABC):
    """BaseValidator: абстрактный класс для validator-плагинов.
    plugin_type = "validator" для автодокументации и фильтрации.
    """
    plugin_type = "validator"
    @abstractmethod
    def validate(self, raw: bytes):
        pass 