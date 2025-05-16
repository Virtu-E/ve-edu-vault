from src.apps.integrations.webhooks.handlers.abstract_type import (
    WebhookHandler,
    WebhookResponse,
)

from ..data_types import WebhookRequestData


class UserRegistrationHandler(WebhookHandler):
    """
    Handles open Edx User Registration events
    """

    def handle(self, payload: WebhookRequestData) -> WebhookResponse:
        return {"status": "success", "message": "User registration successful"}
