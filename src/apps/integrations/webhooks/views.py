import json
import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pydantic import ValidationError

from .data_types import WebhookRequest
from .decorators import qstash_verification_required
from .service import process_webhook_event

log = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def edx_webhook_view(request, *args, **kwargs):
    """EDX webhook handler."""
    return _handle_webhook_request(request)


@csrf_exempt
@require_http_methods(["POST"])
@qstash_verification_required
def qstash_webhook_view(request, *args, **kwargs):
    """QStash webhook handler with verification."""
    return _handle_webhook_request(request)


def _handle_webhook_request(request: HttpRequest) -> JsonResponse:
    """Common webhook handling logic for all webhook sources."""
    log.info("Received webhook request from %s", request.META.get("REMOTE_ADDR"))

    try:
        data = json.loads(request.body)
        log.debug("Successfully parsed webhook JSON payload")

        validated_data = WebhookRequest(**data)
        log.info(
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

        log.info("No handler registered for event type: %s", validated_data.event_type)
        return JsonResponse({"error": "No handler registered for event"}, status=400)

    except json.JSONDecodeError:
        log.error("Failed to decode webhook JSON payload", exc_info=True)
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except KeyError as e:
        log.error(
            "Error processing webhook - missing required field: %s",
            str(e),
            exc_info=True,
        )
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except ValidationError as e:
        log.error("Invalid webhook payload: %s", str(e))
        return JsonResponse({"error": str(e)}, status=400)
