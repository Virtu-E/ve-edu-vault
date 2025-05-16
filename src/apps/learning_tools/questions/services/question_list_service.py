import logging
from typing import List

from src.apps.learning_tools.assessments.util import get_assessment_id
from src.lib.grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from src.repository.grading_response_repository.response_data_types import (
    QuestionAttempt,
)
from src.utils.mixins.context import ServiceResources

log = logging.getLogger(__name__)


async def get_question_attempts(
    *, education_context: ServiceResources
) -> List[QuestionAttempt]:
    """
    Retrieve all question attempts for a specific user and learning objective.

    This function retrieves all grading responses (question attempts) for a given user
    in the context of a specific learning objective and collection. It uses the assessment ID
    associated with the user and learning objective to fetch relevant question attempts.

    Args:
        education_context (ServiceResources): A context object containing resources needed for
            the operation, including:
            - user: The user whose question attempts are being retrieved
            - collection_name: The name of the collection containing the attempts
            - learning_objective: The learning objective associated with the attempts

    Returns:
        List[QuestionAttempt]: A list of QuestionAttempt objects representing the user's
            attempts at answering questions for the specified learning objective.
    """
    user_id = education_context.resources.user.id
    collection_name = education_context.resources.collection_name
    log.debug(
        "Getting grading responses for user %s, collection %s",
        user_id,
        collection_name,
    )

    grading_response_service = GradingResponseService.get_service(
        collection_name=collection_name
    )

    assessment_id = await get_assessment_id(
        user=education_context.resources.user,
        learning_objective=education_context.resources.learning_objective,
    )
    log.debug("Got assessment ID %s for user %s", assessment_id, user_id)

    question_attempts = await grading_response_service.get_grading_responses(
        user_id=user_id,
        collection_name=collection_name,
        assessment_id=assessment_id,
    )
    log.info(
        "Retrieved %d question attempts for user %s",
        len(question_attempts),
        user_id,
    )

    return question_attempts
