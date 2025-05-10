from typing import Any, Dict

from src.apps.integrations.webhooks.handlers.abstract_type import WebhookHandler


class UserRegistrationHandler(WebhookHandler):
    """
    Handles open Edx User Registration events
    """

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
