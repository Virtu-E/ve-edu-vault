import logging
from dataclasses import dataclass
from typing import Optional

from src.apps.learning_tools.questions.models import UserQuestionSet
from src.utils.mixins.question_mixin import QuestionSetResources

from ..exceptions import UserQuestionSetNotFoundError
from ..models import UserAssessmentAttempt

logger = logging.getLogger(__name__)


@dataclass
class OngoingAssessmentData:
    num_questions: int
    assessment: Optional[UserAssessmentAttempt] = None


def get_current_ongoing_assessment(
    *, resources_context: QuestionSetResources
) -> OngoingAssessmentData:
    """
    Retrieve the current ongoing assessment data for a user based on their learning objective.

    This function fetches both the active assessment attempt (if any) and the associated
    question set for the given user and learning objective. It returns a data structure
    containing information about the assessment and number of questions.

    Args:
        resources_context (ServiceResources): Context containing user and learning objective resources.

    Returns:
        OngoingAssessmentData: A data class containing:
            - assessment: The active assessment attempt (if one exists)
            - num_questions: The number of questions in the user's question set

    Raises:
        UserQuestionSetNotFoundError: If no question set is found for the user and learning objective.
    """
    user = resources_context.resources.user
    learning_objective = resources_context.resources.learning_objective

    logger.debug(
        f"Fetching assessment data for user {user.id} and objective {learning_objective.id}"
    )

    try:
        assessment = UserAssessmentAttempt.get_active_attempt(
            user=user, learning_objective=learning_objective
        )

        assessment_questions = UserQuestionSet.objects.get(
            user=user, learning_objective=learning_objective
        )

        logger.debug(f"Successfully gathered assessment data for user {user.id}")

    except UserQuestionSet.DoesNotExist:
        logger.warning(
            f"No question set found for user {user.id} and objective {learning_objective.id}"
        )
        raise UserQuestionSetNotFoundError(user.id, learning_objective.id)

    num_questions = len(list(assessment_questions.question_list_ids))

    if assessment:
        logger.info(
            f"Found active assessment {assessment.assessment_id} with {num_questions} questions"
        )
    else:
        logger.info(
            f"No active assessment found for user {user.id}, returning {num_questions} questions"
        )

    return OngoingAssessmentData(assessment=assessment, num_questions=num_questions)
