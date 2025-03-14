import logging
from typing import Any, Dict, Tuple

from course_sync.course_sync import CourseSyncFactory
from course_sync.data_transformer import StructureExtractor
from course_ware.models import AcademicClass, Course, ExaminationLevel
from course_ware.utils import (
    academic_class_from_course_id,
    get_examination_level_from_course_id,
)
from data_types.course_ware_schema import CourseSyncResponse
from oauth_clients.edx_client import EdxClient
from webhooks.handlers.abstract_type import WebhookHandler

log = logging.getLogger(__name__)


class CourseUpdatedHandler(WebhookHandler):
    """
    Handles OpenEdx Course Update events with improved error handling and response tracking.
    """

    def __init__(self, client: EdxClient):
        self._client = client

    def handle(self, payload: Dict[str, Any]) -> CourseSyncResponse:
        """
        Handles course update webhook.

        Args:
            payload: The webhook payload

        Returns:
            Dict containing status and message
        """

        course_id = payload["course"]["course_key"]

        course_outline = self._client.get_course_outline(course_id)

        course_instance, created = self._get_or_create_course(course_id, course_outline)

        academic_class_instance = self._process_academic_class(course_id)
        sync_result = self._sync_course_structure(
            course_instance,
            academic_class_instance,
            course_outline,
            get_examination_level_from_course_id(course_id),
        )

        status_message = "course created" if created else "course updated"
        return CourseSyncResponse(
            status="success",
            message=f"Course successfully {status_message}",
            course_id=course_id,
            changes_made=sync_result.get("changes_made"),
        )

    @staticmethod
    def _get_or_create_course(
        course_id: str, course_outline: Dict[str, Any]
    ) -> Tuple[Course, bool]:
        """
        Gets or creates course instance with proper change tracking.

        Returns:
            Tuple[Course, bool]: (course_instance, was_created)
        """
        try:
            course_name = course_outline["course_structure"]["display_name"]
            course_instance, created = Course.objects.get_or_create(
                course_key=course_id,
                defaults={"name": course_name, "course_outline": dict()},
            )

            return course_instance, created

        except Exception as e:
            log.error(f"Error creating/updating course {course_id}: {str(e)}")
            raise ValueError(f"Failed to create/update course: {str(e)}")

    @staticmethod
    def _process_academic_class(course_id: str) -> AcademicClass:
        """
        Processes and validates academic class information.

        Returns:
            AcademicClass: The academic class instance
        """
        academic_class = academic_class_from_course_id(course_id)
        if not academic_class:
            raise ValueError(f"No academic class detected for course ID: {course_id}")

        try:
            academic_class_instance, created = AcademicClass.objects.get_or_create(
                name=academic_class
            )
            if created:
                log.info(f"Created new academic class: {academic_class}")
            return academic_class_instance

        except Exception as e:
            log.error(f"Error processing academic class {academic_class}: {str(e)}")
            raise ValueError(f"Failed to process academic class: {str(e)}")

    @staticmethod
    def _sync_course_structure(
        course_instance: Course,
        academic_class_instance: AcademicClass,
        course_outline: Dict[str, Any],
        examination_level: ExaminationLevel,
    ) -> Dict[str, bool]:
        """
        Synchronizes course structure with proper error handling.

        Returns:
            Dict[str, bool]: Dictionary containing:
                - 'success': Whether sync completed without errors
                - 'changes_made': Whether changes were detected and applied
        """
        try:
            sync_result = CourseSyncFactory.create(
                course=course_instance,
                academic_class=academic_class_instance,
                examination_level=examination_level,
                extractor=StructureExtractor,
                new_structure=course_outline,
            ).sync()

            if sync_result:
                log.info(
                    f"Successfully synced course structure for {course_instance.course_key}"
                )
            else:
                log.info(f"No changes detected for course {course_instance.course_key}")

            return {"success": True, "changes_made": sync_result}

        except Exception as e:
            log.error(f"Failed to sync course structure: {str(e)}")
            return {"success": False, "changes_made": False}
