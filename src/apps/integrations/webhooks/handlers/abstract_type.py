from abc import ABC, abstractmethod
from typing import TypedDict

from src.apps.integrations.webhooks.data_types import WebhookRequest


class WebhookResponse(TypedDict):
    status: str
    message: str


class WebhookHandler(ABC):
    """Abstract base class for webhook event handlers"""

    @abstractmethod
    def handle(self, payload: WebhookRequest) -> WebhookResponse:
        """Process the webhook payload and return a response"""
        raise NotImplementedError()
