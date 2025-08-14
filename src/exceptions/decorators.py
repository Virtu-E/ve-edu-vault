import functools
import logging
import uuid
from typing import Callable

from django.http.response import JsonResponse

from src.exceptions import VirtuEducateError
from src.exceptions.handlers import UnifiedAPIErrorHandler

logger = logging.getLogger(__name__)


def handle_virtueducate_errors(
    include_request_id: bool = True,
    log_errors: bool = True,
):
    """
    Decorator that automatically catches and handles VirtuEducate errors.

    Args:
        include_request_id: Whether to generate and include a request ID
        log_errors: Whether to log caught exceptions
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_id = str(uuid.uuid4()) if include_request_id else None

            try:
                return func(*args, **kwargs)
            except VirtuEducateError as e:
                if log_errors:
                    logger.error(
                        "VirtuEducate error in %s: [%s] %s",
                        func.__name__,
                        e.error_code,
                        e.message,
                        exc_info=True,
                        extra={
                            "error_code": e.error_code,
                            "context": e.context,
                            "request_id": request_id,
                            "function": func.__name__,
                        },
                    )

                error_result = UnifiedAPIErrorHandler.handle_exception(e, request_id)
                return JsonResponse(
                    error_result.response.model_dump(), status=error_result.status
                )

        return wrapper

    return decorator
