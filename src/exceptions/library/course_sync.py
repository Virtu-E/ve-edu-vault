from typing import Optional

from src.exceptions import VirtuEducateValidationError


class InvalidChangeDataTypeError(VirtuEducateValidationError):
    """Raised when the wrong change data type is provided for an operation."""

    def __init__(
            self,
            expected_type: str,
            actual_type: str,
            operation: str,
            message: Optional[str] = None,
            error_code: str = "INVALID_CHANGE_DATA_TYPE",
            context: Optional[dict] = None,
            *args,
    ):
        message = message or (
            f"Invalid data type for {operation}. "
            f"Expected {expected_type}, got {actual_type}"
        )
        context = context or {
            "expected_type": expected_type,
            "actual_type": actual_type,
            "operation": operation,
        }
        super().__init__(message, error_code, context, *args)