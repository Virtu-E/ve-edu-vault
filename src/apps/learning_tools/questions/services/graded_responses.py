import logging
from typing import List
from uuid import UUID

from src.apps.learning_tools.assessments.selectors.assessment import AssessmentSelector
from src.repository.graded_responses.data_types import GradedResponse
from src.repository.graded_responses.providers.response_provider import (
    GradingResponseProvider,
)
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


async def get_graded_responses(
    assessment_id: UUID,
    resource_context: QuestionSetResources,
) -> List[GradedResponse]:
    """
    Retrieve all graded responses for a user and assessment.

    Args:
        assessment_id: The assessment ID to retrieve graded responses for
        resource_context: Context containing user and learning objective information

    Returns:
        List[GradedResponse]: List of graded responses for the user
    """
    user_id = resource_context.resources.user.id
    collection_name = resource_context.resources.collection_name

    logger.debug(
        "Getting graded responses for user %s, collection %s, assessment %s",
        user_id,
        collection_name,
        assessment_id,
    )

    provider = GradingResponseProvider.get_mongo_provider(
        collection_name=collection_name
    )
    graded_responses = await provider.get_grading_responses(
        user_id=user_id,
        collection_name=collection_name,
        assessment_id=assessment_id,
    )

    logger.info(
        "Retrieved %d graded responses for user %s, assessment %s",
        len(graded_responses),
        user_id,
        assessment_id,
    )

    return graded_responses


async def save_graded_response(
    graded_response: GradedResponse,
    assessment_id: UUID,
    user_id: str,
    collection_name: str,
) -> None:
    """
    Save a graded response to the database.

    Args:
        graded_response: The graded response to save
        assessment_id: The assessment ID to associate with the graded response
        user_id: The user ID to associate with the graded response
        collection_name: The name of the mongo db collection name

    Raises:
        QuestionAttemptError: If saving the graded response fails
    """

    provider = GradingResponseProvider.get_mongo_provider(
        collection_name=collection_name
    )
    await provider.save_grading_response(
        user_id=user_id,
        question_id=graded_response.question_id,
        assessment_id=assessment_id,
        grading_response=graded_response,
    )

    logger.info(
        "Saved graded response for user %s, question %s, assessment %s",
        user_id,
        graded_response.question_id,
        assessment_id,
    )


async def get_graded_responses_for_current_assessment(
    resource_context: QuestionSetResources,
) -> List[GradedResponse]:
    """
    Convenience function to get graded responses for the current assessment.

    Args:
        resource_context: Context containing user and learning objective information

    Returns:
        List[GradedResponse]: List of graded responses for the current assessment
    """
    selector = AssessmentSelector(resource_context=resource_context)
    assessment_id = await selector.get_assessment_id()

    return await get_graded_responses(assessment_id, resource_context)
