from ..validators.base import BaseValidator


class GeoValidator(BaseValidator):
    """GeoValidator validates subscription data.

    Example:
        validator = GeoValidator()
        result = validator.validate(raw)
    """
    def validate(self, raw: bytes):
        """Validate subscription data.

        Args:
            raw (bytes): Raw data.

        Returns:
            ValidationResult: Result.
        """
        raise NotImplementedError()

