import json
import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pydantic import ValidationError

from src.exceptions import (
    WebhookEventNotSupportedError,
    WebhookJSONDecodeError,
    WebhookMissingFieldError,
    WebhookSchemaValidationError,
)
from src.exceptions.decorators import handle_virtueducate_errors

from .data_types import WebhookRequest
from .decorators import qstash_verification_required
from .service import process_webhook_event

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
@handle_virtueducate_errors(log_errors=True)
def edx_webhook_view(request, *args, **kwargs):
    """EDX webhook handler."""
    return _handle_webhook_request(request)


@csrf_exempt
@require_http_methods(["POST"])
@qstash_verification_required
@handle_virtueducate_errors(log_errors=True)
def qstash_webhook_view(request, *args, **kwargs):
    """QStash webhook handler with verification."""
    return _handle_webhook_request(request)


def _handle_webhook_request(request: HttpRequest) -> JsonResponse:
    """Common webhook handling logic for all webhook sources."""
    logger.info("Received webhook request from %s", request.META.get("REMOTE_ADDR"))

    try:
        data = json.loads(request.body)
        logger.debug("Successfully parsed webhook JSON payload")

        validated_data = WebhookRequest(**data)
        logger.info(
            "Processing webhook event type: %s, ID: %s, timestamp: %s",
            validated_data.event_type,
            validated_data.event_id,
            validated_data.timestamp,
        )

        is_successful = process_webhook_event(webhook_data=validated_data)
        if is_successful:
            return JsonResponse(
                {
                    "status": "received",
                    "event_type": validated_data.event_type,
                    "event_id": validated_data.event_id,
                },
                status=200,
            )

        logger.info(
            "No handler registered for event type: %s", validated_data.event_type
        )
        raise WebhookEventNotSupportedError(
            event_type=validated_data.event_type,
            context={
                "event_id": validated_data.event_id,
                "timestamp": validated_data.timestamp,
            },
        )

    except json.JSONDecodeError as e:
        raise WebhookJSONDecodeError(
            context={"raw_body": request.body.decode("utf-8", errors="ignore")[:500]}
        ) from e

    except KeyError as e:

        field_name = str(e).strip("'\"")
        raise WebhookMissingFieldError(
            field_name=field_name,
            context={"payload_data": request.body.decode("utf-8", errors="ignore")},
        ) from e
    except ValidationError as e:
        raise WebhookSchemaValidationError(
            validation_errors=str(e),
            context={"payload_data": request.body.decode("utf-8", errors="ignore")},
        ) from e
