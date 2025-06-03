from typing import Optional


class VirtuEducateError(Exception):
    """
    Base exception for all VirtuEducate-related errors.

    Attributes:
        message: Human-readable error message
        error_code: Unique error code for programmatic handling
        context: Additional context information
    """

    def __init__(
        self,
        message: str = "An error occurred",
        error_code: Optional[str] = None,
        context: Optional[dict] = None,
        *args,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        super().__init__(self.message, *args)

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def to_dict(self):
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "type": self.__class__.__name__,
        }


class VirtuEducateBusinessError(VirtuEducateError):
    """Base class for business logic violations."""

    pass


class VirtuEducateSystemError(VirtuEducateError):
    """Base class for system-level errors."""

    pass


class VirtuEducateValidationError(VirtuEducateError):
    """Base class for validation errors."""

    pass


class VirtuEducateIntegrationError(VirtuEducateError):
    """Base class for external integration errors."""

    pass
