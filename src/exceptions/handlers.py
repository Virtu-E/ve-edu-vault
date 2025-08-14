from collections import namedtuple
from datetime import datetime, timezone
from typing import Optional

from rest_framework import status

from src.exceptions import (VirtuEducateBusinessError, VirtuEducateError,
                            VirtuEducateSystemError,
                            VirtuEducateValidationError)
from src.exceptions.data_types import ErrorDetail, ErrorResponse

ErrorResult = namedtuple("ErrorResult", ["status", "response"])


class UnifiedAPIErrorHandler:
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
