from abc import ABC, abstractmethod
from typing import TypedDict

from ..data_types import WebhookRequestData


class WebhookResponse(TypedDict):
    status: str
    message: str


class WebhookHandler(ABC):
    """Abstract base class for webhook event handlers"""

    @abstractmethod
    def handle(self, payload: WebhookRequestData) -> WebhookResponse:
        """Process the webhook payload and return a response"""
        raise NotImplementedError()
