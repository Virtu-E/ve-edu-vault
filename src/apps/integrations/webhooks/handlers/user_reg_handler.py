from src.apps.integrations.webhooks.handlers.abstract_type import (
    WebhookHandler,
    WebhookResponse,
)

from ..data_types import WebhookRequest


class UserRegistrationHandler(WebhookHandler):
    """
    Handles open Edx User Registration events
    """

    def handle(self, payload: WebhookRequest) -> WebhookResponse:
        return {"status": "success", "message": "User registration successful"}
