import logging

from .data_types import WebhookRequestData
from .handlers.abstract_type import WebhookHandler, WebhookResponse
from .registry import webhook_registry
from .tasks import process_course_update

log = logging.getLogger(__name__)


def process_webhook_event(*, webhook_data: WebhookRequestData) -> bool:
    event_type = webhook_data.metadata.event_type
    event_id = webhook_data.event_id

    handler = webhook_registry.get_handler(event_type)

    if handler:
        log.info("Found handler for event type: %s, executing handler", event_type)
        handler.handle(webhook_data)
        log.info("Successfully processed event: %s - %s", event_type, event_id)
        return True

    return False


class CourseUpdatedHandlerService(WebhookHandler):
    """Handles OpenEdx Course Update events using celery"""

    def handle(self, payload: WebhookRequestData) -> WebhookResponse:
        process_course_update.delay(payload)
        return {"status": "success", "message": "course queued for updating"}
