from typing import Optional

from src.exceptions import (VirtuEducateBusinessError,
                            VirtuEducateValidationError)


class WebhookValidationError(VirtuEducateValidationError): ...


class WebhookBusinessError(VirtuEducateBusinessError):
    """Base class for webhook business logic errors."""

    pass


class WebhookPayloadError(WebhookValidationError):
    """Raised when webhook payload is malformed or invalid."""

    def __init__(
        self,
        message: str = "Invalid webhook payload",
        error_code: str = "WEBHOOK_INVALID_PAYLOAD",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)


class WebhookJSONDecodeError(WebhookValidationError):
    """Raised when webhook JSON cannot be decoded."""

    def __init__(
        self,
        message: str = "Failed to decode webhook JSON payload",
        error_code: str = "WEBHOOK_JSON_DECODE_ERROR",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)


class WebhookMissingFieldError(WebhookValidationError):
    """Raised when required webhook fields are missing."""

    def __init__(
        self,
        field_name: str,
        message: Optional[str] = None,
        error_code: str = "WEBHOOK_MISSING_FIELD",
        context: Optional[dict] = None,
        *args,
    ):
        message = message or f"Missing required field: {field_name}"
        context = context or {"missing_field": field_name}
        super().__init__(message, error_code, context, *args)


class WebhookSchemaValidationError(WebhookValidationError):
    """Raised when webhook data doesn't match expected schema."""

    def __init__(
        self,
        validation_errors: str,
        message: Optional[str] = None,
        error_code: str = "WEBHOOK_SCHEMA_VALIDATION_ERROR",
        context: Optional[dict] = None,
        *args,
    ):
        message = message or f"Webhook schema validation failed: {validation_errors}"
        context = context or {"validation_errors": validation_errors}
        super().__init__(message, error_code, context, *args)


class WebhookEventNotSupportedError(WebhookBusinessError):
    """Raised when webhook event type is not supported."""

    def __init__(
        self,
        event_type: str,
        message: Optional[str] = None,
        error_code: str = "WEBHOOK_EVENT_NOT_SUPPORTED",
        context: Optional[dict] = None,
        *args,
    ):
        message = message or f"No handler registered for event type: {event_type}"
        context = context or {"event_type": event_type}
        super().__init__(message, error_code, context, *args)
