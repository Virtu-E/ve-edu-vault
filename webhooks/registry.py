from typing import Dict, Optional

from webhooks.handlers import CourseCreatedHandler, CourseUpdatedHandler, WebhookHandler


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
webhook_registry.register("course_published", CourseUpdatedHandler())
