import asyncio
import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from course_sync.side_effects.creation_side_effect import SubTopicCreationSideEffect
from course_ware.models import SubTopic

logger = logging.getLogger(__name__)


@shared_task(
    name="course_sync.side_effects.tasks.process_subtopic_creation_side_effect"
)
def process_subtopic_creation_side_effect(subtopic_id: int) -> None:
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
    try:
        subtopic = SubTopic.objects.get(id=subtopic_id)
    except ObjectDoesNotExist as e:
        logger.error("Subtopic with ID %s does not exist", subtopic_id, exc_info=True)
        raise e

    side_effect = SubTopicCreationSideEffect(subtopic=subtopic)
    # Execute async operations through sync wrapper
    try:
        asyncio.run(side_effect.process_creation_side_effects())

    except asyncio.CancelledError:
        logger.warning("Async operation was cancelled for subtopic ID: %s", subtopic_id)
