import logging
from typing import List, Dict
from asgiref.sync import async_to_sync

from src.repository.question_repository.providers.question_provider import QuestionProvider
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


def fetch_student_questions(*, resource_context: QuestionSetResources) -> List[Dict]:
    """
    Fetch questions for a student based on their question set IDs.

    Args:
        resource_context: Contains question set IDs and user context

    Returns:
        List[Dict]: List of question data dictionaries

    Raises:
        Exception: Any provider or data retrieval errors are logged and re-raised
    """
    question_set_ids = resource_context.resources.question_set_ids
    user_id = resource_context.resources.user.id

    logger.info(
        "Fetching questions for user_id=%s, question_set_count=%d",
        user_id, len(question_set_ids)
    )
    logger.debug("Question set IDs: %s", question_set_ids)

    try:
        question_provider = QuestionProvider.get_mongo_provider(
            resource_context=resource_context
        )

        question_data = async_to_sync(question_provider.get_questions_from_ids)(
            question_set_ids
        )

        logger.info(
            "Successfully fetched %d questions for user_id=%s",
            len(question_data), user_id
        )

        return question_data

    except Exception as e:
        logger.error(
            "Failed to fetch questions for user_id=%s: %s",
            user_id, str(e)
        )
        raise