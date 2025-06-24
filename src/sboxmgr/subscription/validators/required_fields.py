from .base import BaseParsedValidator, register_parsed_validator, ValidationResult
from sboxmgr.subscription.models import PipelineContext

@register_parsed_validator("required_fields")
class RequiredFieldsValidator(BaseParsedValidator):
    """Проверяет обязательные поля ParsedServer: type, address, port, допустимость значений. Возвращает errors и список валидных серверов."""
    def validate(self, servers: list, context: PipelineContext) -> ValidationResult:
        errors = []
        valid_servers = []
        for idx, s in enumerate(servers):
            err = None
            if not hasattr(s, 'type') or not s.type:
                err = f"Server[{idx}]: missing type"
            elif not hasattr(s, 'address') or not s.address:
                err = f"Server[{idx}]: missing address"
            elif not hasattr(s, 'port') or not isinstance(s.port, int) or not (1 <= s.port <= 65535):
                err = f"Server[{idx}]: invalid port: {getattr(s, 'port', None)}"
            if err:
                errors.append(err)
            else:
                valid_servers.append(s)
        result = ValidationResult(valid=bool(valid_servers), errors=errors)
        result.valid_servers = valid_servers
        return result 