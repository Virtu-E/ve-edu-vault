from abc import ABC, abstractmethod
from typing import Any, Dict

from src.services.course_sync.data_types import CourseSyncResponse


class WebhookHandler(ABC):
    """Abstract base class for webhook event handlers"""

    @abstractmethod
    def handle(self, payload: Dict[str, Any]) -> CourseSyncResponse:
        """Process the webhook payload and return a response"""
        raise NotImplementedError()
