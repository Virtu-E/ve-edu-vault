import logging

from src.apps.core.courses.models import AcademicClass, Course
from src.utils.tools import academic_class_from_course_id

from ..data_types import WebhookRequestData
from .abstract_type import WebhookHandler, WebhookResponse

log = logging.getLogger(__name__)


class CourseCreatedHandler(WebhookHandler):
    """Handles OpenEdx Course Creation events"""

    def handle(self, payload: WebhookRequestData) -> WebhookResponse:
        # Process course creation
        course_id = payload.data.course_key
        display_name = payload.data.display_name

        Course.objects.get_or_create(
            course_id=course_id, display_name=display_name, course_outline=dict
        )
        academic_class = academic_class_from_course_id(course_id)
        if academic_class:
            AcademicClass.objects.get_or_create(name=academic_class)
        log.info("Created course %s", course_id)

        return {"status": "course created", "message": "course created successfully"}
