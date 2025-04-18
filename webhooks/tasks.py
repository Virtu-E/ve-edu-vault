import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync
from celery import shared_task

from course_sync.course_sync import CourseSyncService
from oauth_clients.edx_client import EdxClient
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
        edx_client = EdxClient(client=client)
        new_course_outline = await edx_client.get_course_outline(course_id=course_id)
        log.debug(f"Successfully retrieved course outline for: {course_id}")

    log.info(f"Initializing CourseUpdatedHandler for course: {course_id}")
    handler = CourseUpdatedHandler(
        new_course_outline_dict=new_course_outline, sync_service=sync_service
    )

    log.info(f"Processing course update for course: {course_id}")
    result = await asyncio.to_thread(handler.handle, payload)

    log.info(f"Course update processing completed successfully for: {course_id}")
    return result.model_dump()


@shared_task(
    name="course_ware.tasks.process_course_update",
    max_retries=3,
    default_retry_delay=60,
    ignore_result=True,
)
def process_course_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task to process course updates asynchronously"""
    course_id = payload.get("course", {}).get("course_key", "unknown")

    log.info(f"Starting Celery task process_course_update for course: {course_id}")

    log.debug(f"Task payload: {payload}")
    result = async_to_sync(_process_course_update_async)(payload)
    log.info(f"Celery task completed successfully for course: {course_id}")
    return result
