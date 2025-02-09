import logging
from typing import Any, Dict

from celery import shared_task

from webhooks.handlers import CourseUpdatedHandler

log = logging.getLogger(__name__)


@shared_task(
    name="course_ware.tasks.process_course_update",
    max_retries=3,
    default_retry_delay=60,
)
def process_course_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task to process course updates asynchronously"""
    handler = CourseUpdatedHandler()
    result = handler.handle(payload)
    return result.model_dump()
