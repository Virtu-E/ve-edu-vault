import logging
from uuid import UUID

from asgiref.sync import sync_to_async

from course_ware.models import EdxUser, LearningObjective, UserAssessmentAttempt

logger = logging.getLogger(__name__)


async def get_assessment_id(
    user: EdxUser, learning_objective: LearningObjective
) -> UUID:
    """
    Retrieves or creates an assessment attempt for the given user and learning_objective.

    Args:
        user (EdxUser): The user for whom to get/create the assessment
        learning_objective (LearningObjective): The learning objective to assess

    Returns:
        UUID: The assessment ID for the user's attempt
    """
    logger.debug(
        f"Getting assessment for user={user.id}, objective={learning_objective.id}"
    )
    attempt, _ = await sync_to_async(UserAssessmentAttempt.get_or_create_attempt)(
        user, learning_objective
    )
    logger.debug(f"Assessment ID: {attempt.assessment_id}")
    return attempt.assessment_id
