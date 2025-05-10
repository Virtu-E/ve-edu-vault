from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple


class WebhookValidator(ABC):
    @abstractmethod
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the webhook payload structure.
        Returns:
             Tuple[bool, str]: (is_valid, error_message)
        """
        raise NotImplementedError()


class EdxWebhookValidator(WebhookValidator):
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        if not payload:
            return False, "Empty payload received"

        if not isinstance(payload.get("course", {}), dict):
            return False, "Invalid course data structure"

        if not payload.get("course", {}).get("course_key"):
            return False, "Missing course key in payload"

        return True, ""
