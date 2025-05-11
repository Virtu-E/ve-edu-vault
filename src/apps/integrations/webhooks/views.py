import json
import logging
from typing import Optional, Tuple

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from src.apps.integrations.webhooks.registry import webhook_registry

log = logging.getLogger(__name__)


def _validate_payload(data) -> Tuple[bool, Optional[str]]:
    """
    Validate the webhook payload structure

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        log.warning("Webhook payload is not a dictionary")
        return False, "Invalid payload format"

    metadata = data.get("event_metadata")
    if not metadata:
        log.warning("Webhook payload missing event_metadata")
        return False, "Missing event_metadata"

    event_type = metadata.get("event_type")
    if not event_type:
        log.warning("Webhook metadata missing event_type")
        return False, "Missing event_type in metadata"

    log.debug("Webhook payload validation successful")
    return True, None


@csrf_exempt
@require_http_methods(["POST"])
def webhook_view(request, *args, **kwargs):
    """
    Main webhook handler that processes incoming webhook events.
    """
    log.info("Received webhook request from %s", request.META.get("REMOTE_ADDR"))

    try:
        data = json.loads(request.body)
        log.debug("Successfully parsed webhook JSON payload")

        is_valid, error_message = _validate_payload(data)
        if not is_valid:
            log.warning("Invalid webhook payload: %s", error_message)
            return JsonResponse({"error": error_message}, status=400)

        metadata = data["event_metadata"]
        event_type = metadata["event_type"]
        event_id = metadata.get("event_id", "unknown")
        timestamp = metadata.get("timestamp")

        log.info(
            "Processing webhook event type: %s, ID: %s, timestamp: %s",
            event_type,
            event_id,
            timestamp,
        )

        course_key = data.get("data", {}).get("course_key", "")
        if course_key:
            log.debug("Event associated with course_key: %s", course_key)

        cache_key = f"webhook:{event_type}:{event_id}:{course_key}"

        # Remove print statement and replace with proper logging
        log.debug("Event timestamp: %s", timestamp)

        if cache.get(cache_key):
            log.info(
                "Duplicate event detected: %s - %s - %s",
                event_type,
                event_id,
                course_key,
            )
            return JsonResponse(
                {
                    "status": "already_processed",
                    "event_type": event_type,
                    "event_id": event_id,
                },
                status=200,
            )

        log.debug("Setting cache for event: %s", cache_key)
        cache.set(cache_key, True, timeout=3600)

        handler = webhook_registry.get_handler(event_type)

        if handler:
            log.info("Found handler for event type: %s, executing handler", event_type)
            try:
                handler.handle(data)
                log.info("Successfully processed event: %s - %s", event_type, event_id)
            except Exception as e:
                log.error(
                    "Handler error for event %s - %s: %s",
                    event_type,
                    event_id,
                    str(e),
                    exc_info=True,
                )
                return JsonResponse(
                    {
                        "status": "error",
                        "event_type": event_type,
                        "event_id": event_id,
                        "error": "Handler processing error",
                    },
                    status=500,
                )

            response_data = {
                "status": "success",
                "event_type": event_type,
                "event_id": event_id,
            }

            return JsonResponse(response_data, status=200)
        else:
            # No handler found, but still return 200 as requested
            log.info("No handler registered for event type: %s", event_type)
            return JsonResponse(
                {
                    "status": "received",
                    "event_type": event_type,
                    "event_id": event_id,
                },
                status=200,
            )

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
    except Exception as e:
        log.error("Unexpected error processing webhook: %s", str(e), exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
