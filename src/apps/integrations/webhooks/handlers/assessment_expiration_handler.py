from ..data_types import WebhookRequest
from ..handlers.abstract_type import WebhookHandler, WebhookResponse


class AssessmentExpirationHandler(WebhookHandler):
    """
    Handles Assessment Expiration
    """

    def handle(self, payload: WebhookRequest) -> WebhookResponse:
        print(payload)
        print("hello world")
        return {"status": "success", "message": "User registration successful"}
