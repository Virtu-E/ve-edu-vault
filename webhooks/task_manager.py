import logging
from typing import Any, Dict

from data_types.course_ware_schema import CourseSyncResponse
from webhooks.handlers.abstract_type import WebhookHandler
from webhooks.tasks import process_course_update
from webhooks.validators import WebhookValidator

log = logging.getLogger(__name__)


class CourseTaskManager(WebhookHandler):
    def __init__(self, validator: WebhookValidator):
        self._validator = validator

    def handle(self, payload: Dict[str, Any]) -> CourseSyncResponse:
        is_valid, error_message = self._validator.validate_payload(payload)
        if not is_valid:
            log.error(f"Invalid payload: {error_message}")
            return CourseSyncResponse(
                status="error",
                message=f"Invalid payload: {error_message}",
                course_id="",
                changes_made=False,
            )

        payload = {
            "course": {
                "course_key": payload["course"]["course_key"],
            }
        }

        try:
            process_course_update.delay(payload),

            return CourseSyncResponse(
                status="pending",
                message="Course update workflow initiated",
                course_id=payload["course"]["course_key"],
                changes_made=False,
            )

        except Exception as e:
            log.exception("Failed to initiate course update workflow")
            return CourseSyncResponse(
                status="error",
                message=f"Failed to queue tasks: {str(e)}",
                course_id=payload["course"]["course_key"],
                changes_made=False,
            )
