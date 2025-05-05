import asyncio
import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from redis.exceptions import LockError

from course_sync.default_question_service import DefaultQuestionService
from course_ware.models import LearningObjective
from edu_vault.settings import common

REDIS_CLIENT = common.REDIS_CLIENT

logger = logging.getLogger(__name__)


@shared_task(
    name="course_sync.tasks.add_default_question_set",
    max_retries=3,
    default_retry_delay=30,
    ignore_result=True,
)
def add_default_question_set(objective_id: int) -> None:
    """
    Creates/updates the default question set for a given
    learning objective pk with distributed locking to prevent
    concurrent operations on the same objective.

    Args:
        objective_id: The ID of the Learning Objective
    """
    # Create a lock with a timeout (in seconds)
    lock_name = f"lock:add_default_question_set:{objective_id}"
    lock_timeout = 120  # 2 minutes max lock time

    # Try to acquire the lock
    lock = REDIS_CLIENT.lock(lock_name, timeout=lock_timeout)
    try:
        if lock.acquire(blocking=False):
            try:
                logger.info(
                    "Starting default question set creation for objective ID: %s",
                    objective_id,
                )
                _process_default_question_set(objective_id)
                logger.info(
                    "Successfully completed default question set creation for objective ID: %s",
                    objective_id,
                )
            finally:
                # Always release the lock when done
                lock.release()
        else:
            # Task is already running, reschedule for later
            logger.info(
                "Task for objective ID %s is already running. Rescheduling.",
                objective_id,
            )
            add_default_question_set.apply_async(
                args=[objective_id], countdown=45  # Try again after 45 seconds
            )
    except LockError:
        # Handle potential lock errors
        logger.error("Lock error occurred for objective ID %s", objective_id)
        add_default_question_set.retry(countdown=30)


def _process_default_question_set(objective_id: int) -> None:
    """Helper function to process the default question set for an objective"""
    try:
        objective = LearningObjective.objects.get(id=objective_id)
        sub_topic = objective.sub_topic
        collection_name = sub_topic.topic.course.course_key

    except ObjectDoesNotExist as e:
        logger.error(
            "Learning Objective with ID %s does not exist", objective_id, exc_info=True
        )
        raise e

    # Execute async operations through sync wrapper
    service = DefaultQuestionService()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            service.process_default_question(
                objective=objective, collection_name=collection_name
            )
        )
    except asyncio.CancelledError:
        logger.warning(
            "Async operation was cancelled for objective ID: %s", objective_id
        )
    finally:
        loop.close()
