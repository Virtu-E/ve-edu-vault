import logging
from typing import Any, Dict

from data_types.course_ware_schema import CourseSyncResponse
from webhooks.handlers.abstract_type import WebhookHandler
from webhooks.tasks import process_course_update
from webhooks.validators import WebhookValidator

log = logging.getLogger(__name__)


class CourseTaskManager(WebhookHandler):
    """
    Manages the handling of course-related webhook events.

    This class is responsible for validating incoming webhook payloads,
    extracting relevant course information, and dispatching asynchronous
    course update tasks via Celery.

    Attributes:
        _validator: An instance of WebhookValidator used to validate incoming payloads
    """

    def __init__(self, validator: WebhookValidator):
        """
        Initialize the CourseTaskManager with a validator.

        Args:
            validator: The WebhookValidator instance used to validate webhook payloads
        """
        self._validator = validator
        log.debug("CourseTaskManager initialized with validator")

    def handle(self, payload: Dict[str, Any]) -> CourseSyncResponse:
        """
        Process incoming webhook payload for course updates.

        Args:
            payload: The webhook payload containing course update information

        Returns:
            CourseSyncResponse: A response object indicating the status of the operation
        """
        course_id = payload.get("course", {}).get("course_key", "unknown")
        log.info(f"Handling course update webhook for course_id: {course_id}")

        # Validate the incoming payload
        log.debug(f"Validating payload for course_id: {course_id}")
        is_valid, error_message = self._validator.validate_payload(payload)
        if not is_valid:
            log.error(f"Invalid payload for course_id {course_id}: {error_message}")
            return CourseSyncResponse(
                status="error",
                message=f"Invalid payload: {error_message}",
                course_id="",
                changes_made=False,
            )

        log.debug(f"Extracting course information for course_id: {course_id}")
        task_payload = {
            "course": {
                "course_key": payload["course"]["course_key"],
            }
        }

        try:
            log.info(f"Dispatching course update task for course_id: {course_id}")

            task = process_course_update.delay(task_payload)

            log.debug(
                f"Task dispatched successfully with task_id: {task.id} for course_id: {course_id}"
            )

            return CourseSyncResponse(
                status="pending",
                message="Course update workflow initiated",
                course_id=course_id,
                changes_made=False,
            )

        except Exception as e:
            log.exception(
                f"Failed to initiate course update workflow for course_id: {course_id}",
                exc_info=True,
            )
            return CourseSyncResponse(
                status="error",
                message=f"Failed to queue tasks: {str(e)}",
                course_id=course_id,
                changes_made=False,
            )
