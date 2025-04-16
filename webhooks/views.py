import json
import logging
from typing import Optional, Tuple

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from webhooks.registry import webhook_registry

log = logging.getLogger(__name__)


def _validate_payload(data) -> Tuple[bool, Optional[str]]:
    """
    Validate the webhook payload structure

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Invalid payload format"

    metadata = data.get("event_metadata")
    if not metadata:
        return False, "Missing event_metadata"

    event_type = metadata.get("event_type")
    if not event_type:
        return False, "Missing event_type in metadata"

    return True, None


@csrf_exempt
@require_http_methods(["POST"])
def webhook_view(request, *args, **kwargs):

    try:
        # Parse JSON data from request body
        data = json.loads(request.body)

        # Validate payload structure
        is_valid, error_message = _validate_payload(data)
        if not is_valid:
            return JsonResponse({"error": error_message}, status=400)

        # Extract event metadata and type
        metadata = data["event_metadata"]
        event_type = metadata["event_type"]

        # Get the appropriate handler
        handler = webhook_registry.get_handler(event_type)

        if handler:
            handler.handle(data)

            response_data = {
                "status": "success",
                "event_type": event_type,
                "event_id": metadata.get("id"),
            }

            return JsonResponse(response_data, status=200)
        else:
            # No handler found, but still return 200 as requested
            log.info(f"No handler registered for event type: {event_type}")
            return JsonResponse(
                {
                    "status": "received",
                    "event_type": event_type,
                    "event_id": metadata.get("id"),
                },
                status=200,
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
    except KeyError as e:
        log.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)
