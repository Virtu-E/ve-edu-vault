import logging
from typing import Any, Dict, Tuple

from src.apps.core.courses.models import AcademicClass, Course, ExaminationLevel
from src.exceptions import WebhookMissingFieldError
from src.library.course_sync.course_sync import ChangeResult, CourseSyncService
from src.library.course_sync.data_transformer import EdxDataTransformer
from src.library.course_sync.data_types import EdxCourseOutline
from src.utils.tools import (
    academic_class_from_course_id,
    get_examination_level_from_course_id,
)

from ..data_types import WebhookRequest
from ..tasks import process_course_update
from .abstract_type import WebhookHandler, WebhookResponse

logger = logging.getLogger(__name__)


class CourseUpdatedHandlerCelery(WebhookHandler):
    """Handles OpenEdx Course Update events using celery"""

    def handle(self, payload: WebhookRequest) -> WebhookResponse:
        process_course_update.delay(payload)
        return {"status": "success", "message": "course queued for updating"}


class CourseUpdatedHandler(WebhookHandler):
    """
    Handles OpenEdx Course Update events
    """

    def __init__(self, sync_service: CourseSyncService, new_course_outline_dict: Dict):
        self._sync_service = sync_service
        self._new_course_outline_dict = new_course_outline_dict

    def handle(self, payload: WebhookRequest) -> WebhookResponse:
        """
        Handles course update webhook.

        Args:
            payload: The webhook payload

        Returns:
            Dict containing status and message
        """

        course_id = payload.data.course_key

        course, created = self._get_or_create_course(
            course_id, self._new_course_outline_dict
        )

        academic_class = self._process_academic_class(course_id)
        transformed_course_outline = EdxDataTransformer.transform_to_course_outline(
            course_id=course_id,
            structure=self._new_course_outline_dict,
            title=course.name,
        )
        sync_result = self._sync_course_structure(
            course=course,
            academic_class=academic_class,
            new_course_outline=transformed_course_outline,
            examination_level=get_examination_level_from_course_id(course_id),
        )

        changes_made = sync_result.num_success > 0
        failed_results = sync_result.num_failed > 0

        status_message = "course created" if created else "course updated"

        if not failed_results:
            course.course_outline = self._new_course_outline_dict
            course.save()

        logging.info(
            "Response message: %s",
            {
                "course_id": course_id,
                "changes_made": changes_made,
                "num_success": sync_result.num_success,
                "num_failed": sync_result.num_failed,
                "status_message": status_message,
            },
        )

        return {"status": "success", "message": f"Course Successfully {status_message}"}

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
                defaults={"name": course_name, "course_outline": dict},
            )

            return course_instance, created

        except KeyError as e:
            logger.error(
                f"Error creating/updating course {course_id}: {str(e)}", exc_info=True
            )
            raise WebhookMissingFieldError(
                field_name="course_id",
            ) from e

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

        academic_class_instance, created = AcademicClass.objects.get_or_create(
            name=academic_class
        )
        if created:
            logger.info(f"Created new academic class: {academic_class}")
        return academic_class_instance

    def _sync_course_structure(
        self,
        course: Course,
        academic_class: AcademicClass,
        new_course_outline: EdxCourseOutline,
        examination_level: ExaminationLevel,
    ) -> ChangeResult:
        """
        Synchronizes course structure between the provided course and new course outline.

        Args:
            course: The course object to be synchronized
            academic_class: The academic class associated with the course
            new_course_outline: The new course outline to sync with
            examination_level: The examination level for the course

        Returns:
            ChangeResult: Object containing the results of the synchronization operation
        """

        return self._sync_service.sync_course(
            new_course_outline=new_course_outline,
            course=course,
            examination_level=examination_level,
            academic_class=academic_class,
        )
