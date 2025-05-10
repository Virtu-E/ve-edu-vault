import asyncio
import logging
from typing import Any, Dict

from asgiref.sync import async_to_sync
from celery import shared_task
from redis.exceptions import LockError

from src.services.course_sync.course_sync import CourseSyncService
from src.edu_vault.settings import common
from src.apps.integrations.oauth_clients.edx_client import EdxClient
from src.apps.integrations.oauth_clients.services import OAuthClient
from src.apps.integrations.webhooks.handlers.course_update_handler import (
    CourseUpdatedHandler,
)

REDIS_CLIENT = common.REDIS_CLIENT

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
def process_course_update(payload: Dict[str, Any]) -> None:
    """Celery task to process course updates asynchronously with lock"""
    course_id = payload.get("course", {}).get("course_key", "unknown")

    # Create a lock with a timeout (in seconds)
    lock_name = f"lock:process_course_update:{course_id}"
    lock_timeout = 3600  # 1 hour max lock time

    # Try to acquire the lock
    lock = REDIS_CLIENT.lock(lock_name, timeout=lock_timeout)
    try:
        if lock.acquire(blocking=False):
            try:
                log.info(
                    f"Starting Celery task process_course_update for course: {course_id}"
                )
                log.debug(f"Task payload: {payload}")
                async_to_sync(_process_course_update_async)(payload)
                log.info(f"Celery task completed successfully for course: {course_id}")
            finally:
                # Always release the lock when done
                lock.release()
        else:
            # Task is already running, reschedule for later
            log.info(f"Task for course {course_id} is already running. Rescheduling.")
            process_course_update.apply_async(
                args=[payload], countdown=60  # Try again after 1 minute
            )
    except LockError:
        # Handle potential lock errors
        log.error(f"Lock error occurred for course {course_id}")
        process_course_update.retry(countdown=30)
