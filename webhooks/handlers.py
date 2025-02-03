import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

from course_sync.main import CourseSync
from course_ware.models import AcademicClass, Course
from course_ware.utils import (
    academic_class_from_course_id,
    get_examination_level_from_course_id,
)

logger = logging.getLogger(__name__)


class WebhookHandler(ABC):
    """Abstract base class for webhook event handlers"""

    @abstractmethod
    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process the webhook payload and return a response"""
        raise NotImplementedError()


class CourseCreatedHandler(WebhookHandler):
    """Handles OpenEdx Course Creation events"""

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Process course creation
        course_id = payload["course"]["course_key"]
        display_name = payload["course"]["display_name"]

        Course.objects.get_or_create(course_id=course_id, display_name=display_name, course_outline=dict())
        academic_class = academic_class_from_course_id(course_id)
        if academic_class:
            AcademicClass.objects.get_or_create(name=academic_class)
        logger.info("Created course %s", course_id)

        return {"status": "course created", "message": "course created successfully"}


class CourseUpdatedHandler(WebhookHandler):
    """
    Handles OpenEdx Course Update events with improved error handling and response tracking.
    """

    def _validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates the webhook payload structure.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not payload:
            return False, "Empty payload received"

        if not isinstance(payload.get("course", {}), dict):
            return False, "Invalid course data structure"

        if not payload.get("course", {}).get("course_key"):
            return False, "Missing course key in payload"

        return True, ""

    def _get_or_update_course(self, course_id: str, course_outline: Dict[str, Any]) -> Tuple[Course, bool]:
        """
        Gets or updates course instance with proper change tracking.

        Returns:
            Tuple[Course, bool]: (course_instance, was_created)
        """
        try:
            course_name = course_outline["course_structure"]["display_name"]
            course_instance, created = Course.objects.get_or_create(
                course_key=course_id,
                defaults={"name": course_name, "course_outline": course_outline},
            )

            return course_instance, created

        except Exception as e:
            logger.error(f"Error creating/updating course {course_id}: {str(e)}")
            raise ValueError(f"Failed to create/update course: {str(e)}")

    def _process_academic_class(self, course_id: str) -> AcademicClass:
        """
        Processes and validates academic class information.

        Returns:
            AcademicClass: The academic class instance
        """
        academic_class = academic_class_from_course_id(course_id)
        if not academic_class:
            raise ValueError(f"No academic class detected for course ID: {course_id}")

        try:
            academic_class_instance, created = AcademicClass.objects.get_or_create(name=academic_class)
            if created:
                logger.info(f"Created new academic class: {academic_class}")
            return academic_class_instance

        except Exception as e:
            logger.error(f"Error processing academic class {academic_class}: {str(e)}")
            raise ValueError(f"Failed to process academic class: {str(e)}")

    def _sync_course_structure(
        self,
        course_instance: Course,
        academic_class_instance: AcademicClass,
        course_outline: Dict[str, Any],
        examination_level: str,
    ) -> bool:
        """
        Synchronizes course structure with proper error handling.

        Returns:
            bool: Whether sync was successful
        """
        sync_result = CourseSync(
            course=course_instance,
            academic_class=academic_class_instance,
            new_structure=course_outline,
            examination_level=examination_level,
        ).sync()

        if sync_result:
            logger.info(f"Successfully synced course structure for {course_instance.course_key}")
        else:
            logger.info(f"No changes detected for course {course_instance.course_key}")

        return True

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles course update webhook.

        Args:
            payload: The webhook payload

        Returns:
            Dict containing status and message
        """
        is_valid, error_message = self._validate_payload(payload)
        if not is_valid:
            logger.error(f"Invalid payload: {error_message}")
            return {"status": "error", "message": f"Invalid payload: {error_message}"}

        course_id = payload["course"]["course_key"]

        # course_outline = get_course_outline(course_id)
        course_outline = payload["course"]["course_outline"]

        course_instance, created = self._get_or_update_course(course_id, course_outline)

        academic_class_instance = self._process_academic_class(course_id)
        self._sync_course_structure(
            course_instance,
            academic_class_instance,
            course_outline,
            get_examination_level_from_course_id(course_id),
        )

        status_message = "course created" if created else "course updated"
        return {
            "status": "success",
            "message": f"Course successfully {status_message}",
            "course_id": course_id,
            "created": created,
        }


class UserRegistrationHandler(WebhookHandler):
    """
    Handles open Edx User Registration events
    """

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
