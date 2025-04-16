import asyncio
import logging
from typing import Any, Dict

from celery import shared_task

from course_sync.course_sync import CourseSyncService
from oauth_clients.services import OAuthClient
from webhooks.handlers.course_update_handler import CourseUpdatedHandler

log = logging.getLogger(__name__)


async def _process_course_update_async(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Async implementation of the course update processing"""
    course_id = payload.get("course", {}).get("course_key")

    log.info(f"Starting async course update processing for course_id: {course_id}")
    log.debug(f"Initializing CourseSyncService for course: {course_id}")
    sync_service = CourseSyncService.create_service()

    log.info(f"Fetching course outline from OpenEdX for course: {course_id}")
    async with OAuthClient(service_type="OPENEDX") as client:
        new_course_outline = await client.get_course_outline(course_id=course_id)
        log.debug(f"Successfully retrieved course outline for: {course_id}")

    log.info(f"Initializing CourseUpdatedHandler for course: {course_id}")
    handler = CourseUpdatedHandler(
        new_course_outline_dict=new_course_outline, sync_service=sync_service
    )

    log.info(f"Processing course update for course: {course_id}")
    result = handler.handle(payload)

    log.info(f"Course update processing completed successfully for: {course_id}")
    return result.model_dump()


@shared_task(
    name="course_ware.tasks.process_course_update",
    max_retries=3,
    default_retry_delay=60,
)
def process_course_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task to process course updates asynchronously"""
    task_id = asyncio.current_task().get_name() if asyncio.current_task() else "unknown"
    course_id = payload.get("course", {}).get("course_key", "unknown")

    log.info(
        f"Starting Celery task process_course_update for course: {course_id}, task_id: {task_id}"
    )

    log.debug(f"Task payload: {payload}")
    result = asyncio.run(_process_course_update_async(payload))
    log.info(
        f"Celery task completed successfully for course: {course_id}, task_id: {task_id}"
    )
    return result
