from typing import Dict, Optional

from src.apps.integrations.webhooks.handlers.abstract_type import WebhookHandler
from src.apps.integrations.webhooks.handlers.course_create_handler import (
    CourseCreatedHandler,
)
from src.apps.integrations.webhooks.task_manager import CourseTaskManager
from src.apps.integrations.webhooks.validators import EdxWebhookValidator


class WebhookRegistry:
    """Registry for webhook handlers"""

    def __init__(self):
        self._handlers: Dict[str, WebhookHandler] = {}

    def register(self, event_type: str, handler: WebhookHandler) -> None:
        """Register a handler for an event type"""
        self._handlers[event_type] = handler

    def get_handler(self, event_type: str) -> Optional[WebhookHandler]:
        """Get the handler for an event type"""
        return self._handlers.get(event_type)


webhook_registry = WebhookRegistry()

# Register handlers
webhook_registry.register(
    "org.openedx.content_authoring.course.created.v1", CourseCreatedHandler()
)
webhook_registry.register("course_published", CourseTaskManager(EdxWebhookValidator()))
