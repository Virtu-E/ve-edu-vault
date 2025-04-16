import logging
from typing import Any, Dict

from course_ware.models import AcademicClass, Course
from course_ware.utils import academic_class_from_course_id
from webhooks.handlers.abstract_type import WebhookHandler

log = logging.getLogger(__name__)


class CourseCreatedHandler(WebhookHandler):
    """Handles OpenEdx Course Creation events"""

    def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Process course creation
        course_id = payload["course"]["course_key"]
        display_name = payload["course"]["display_name"]

        Course.objects.get_or_create(
            course_id=course_id, display_name=display_name, course_outline=dict
        )
        academic_class = academic_class_from_course_id(course_id)
        if academic_class:
            AcademicClass.objects.get_or_create(name=academic_class)
        log.info("Created course %s", course_id)

        return {"status": "course created", "message": "course created successfully"}
