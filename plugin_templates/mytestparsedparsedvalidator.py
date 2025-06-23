from ..validators.base import register_parsed_validator
from ..validators.base import BaseParsedValidator
from ..models import SubscriptionSource, ParsedServer


@register_parsed_validator("custom_parsed_validator")
class MyTestParsedParsedValidator(BaseParsedValidator):
    """MyTestParsedParsedValidator validates parsed servers.

Example:
    validator = MyTestParsedParsedValidator()
    result = validator.validate(servers, context)"""

def validate(self, servers, context):

    """Validate parsed servers.

    Args:
        servers (list[ParsedServer]): List of parsed servers.
        context (PipelineContext): Pipeline context.

    Returns:
        ValidationResult: Result.
    """
    raise NotImplementedError()

