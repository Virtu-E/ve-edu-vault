from collections import namedtuple
from datetime import datetime, timezone
from typing import Optional

from rest_framework import status

from src.exceptions import (
    VirtuEducateBusinessError,
    VirtuEducateError,
    VirtuEducateSystemError,
    VirtuEducateValidationError,
)
from src.exceptions.data_types import ErrorDetail, ErrorResponse

ErrorResult = namedtuple("ErrorResult", ["status", "response"])


class ErrorHandlerMeta(type):
    """Metaclass that validates error handler methods only accept VirtuEducate errors"""

    def __new__(mcs, name, bases, namespace, **kwargs):
        # Get the new class
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        if "create_error_detail" in namespace:
            original_method = namespace["create_error_detail"]
            cls.create_error_detail = mcs._wrap_method(
                original_method, "create_error_detail"
            )

        return cls

    @staticmethod
    def _wrap_method(method, method_name):
        """Wrap method to validate exception type"""

        def wrapper(*args, **kwargs):
            # Find the exception parameter
            if len(args) >= 2:  # cls/self + exception
                exception = args[1]
            elif "exception" in kwargs:
                exception = kwargs["exception"]
            else:
                raise ValueError(f"{method_name} must receive an exception parameter")

            if not isinstance(exception, VirtuEducateError):
                raise TypeError(
                    f"{method_name} only handles VirtuEducateError instances. "
                    f"Got {type(exception).__name__}: {exception}"
                )

            return method(*args, **kwargs)

        return wrapper


class UnifiedAPIErrorHandler(metaclass=ErrorHandlerMeta):
    """Handles conversion of exceptions to standardized error responses"""

    @staticmethod
    def get_http_status(exception: Exception) -> int:
        """Map exception types to HTTP status codes"""
        if isinstance(exception, VirtuEducateValidationError):
            return status.HTTP_400_BAD_REQUEST
        elif isinstance(exception, VirtuEducateBusinessError):
            return status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exception, VirtuEducateSystemError):
            return status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    @staticmethod
    def create_error_detail(exception: VirtuEducateError) -> ErrorDetail:
        """Convert VirtuEducate exception to ErrorDetail - ONLY accepts VirtuEducate errors"""
        return ErrorDetail(
            code=getattr(exception, "error_code", exception.__class__.__name__),
            message=str(exception),
            context=getattr(exception, "context", None),
        )

    @classmethod
    def handle_exception(
        cls, exception: VirtuEducateError, request_id: Optional[str] = None
    ) -> ErrorResult:
        """Convert exception to ErrorResponse and HTTP status"""
        error_detail = cls.create_error_detail(exception)
        http_status = cls.get_http_status(exception)
        error_response = ErrorResponse(
            success=False,
            errors=[error_detail],
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return ErrorResult(status=http_status, response=error_response)
