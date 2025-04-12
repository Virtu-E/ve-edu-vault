import asyncio
import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from course_sync.side_effects.creation_side_effect import SubTopicCreationSideEffect
from course_ware.models import SubTopic

logger = logging.getLogger(__name__)


@shared_task(
    name="course_sync.tasks.subtopic_creation_side_effect",
    ignore_result=False,  # Changed to track task results
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(
        DatabaseError,
        ConnectionError,
        TimeoutError,
    ),  # Auto-retry for common errors
    retry_backoff=True,  # Use exponential backoff
    retry_backoff_max=300,  # Maximum retry delay
    acks_late=True,  # Only acknowledge after task completes or fails
    task_time_limit=300,  # 5-minute timeout
)
def process_subtopic_creation_side_effect(subtopic_id: int) -> bool:
    """
    Process side effects for a newly created subtopic.

    Args:
        subtopic_id: The ID of the subtopic to process

    Returns:
        Boolean indicating success or failure
    """
    logger.info(
        "Starting subtopic creation side effects for subtopic ID: %s", subtopic_id
    )

    # Get current task instance for retries
    task = process_subtopic_creation_side_effect

    try:
        try:
            subtopic = SubTopic.objects.get(pk=subtopic_id)
        except ObjectDoesNotExist:
            logger.error("Subtopic with ID %s does not exist", subtopic_id)
            return False

        side_effect = SubTopicCreationSideEffect(subtopic=subtopic)
        # Execute async operations through sync wrapper
        try:
            # Run the async process_creation_side_effects in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(side_effect.process_creation_side_effects())
                logger.info(
                    "Successfully processed side effects for subtopic ID: %s",
                    subtopic_id,
                )
                return True
            finally:
                loop.close()

        except asyncio.CancelledError:
            logger.warning(
                "Async operation was cancelled for subtopic ID: %s", subtopic_id
            )
            raise task.retry()

    except MaxRetriesExceededError:
        logger.error(
            "Maximum retries exceeded for subtopic ID %s. Side effects were not fully processed.",
            subtopic_id,
        )
        # Consider sending alert or notification here
        return False

    return True
