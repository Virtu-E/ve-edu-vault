from enum import Enum
from typing import Dict, Optional

from src.apps.integrations.webhooks.handlers.abstract_type import WebhookHandler
from src.apps.integrations.webhooks.handlers.course_create_handler import (
    CourseCreatedHandler,
)

from .handlers.assessment_expiration_handler import AssessmentExpirationHandler
from .handlers.course_update_handler import CourseUpdatedHandlerCelery


class HandlerTypeEnum(Enum):
    COURSE_CREATED = "org.openedx.content_authoring.course.created.v1"
    COURSE_PUBLISHED = "course_published"
    ASSESSMENT_EXPIRATION = "assessment_expiration"


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
webhook_registry.register(HandlerTypeEnum.COURSE_CREATED.value, CourseCreatedHandler())
webhook_registry.register(
    HandlerTypeEnum.COURSE_PUBLISHED.value, CourseUpdatedHandlerCelery()
)
webhook_registry.register(
    HandlerTypeEnum.ASSESSMENT_EXPIRATION.value, AssessmentExpirationHandler()
)
