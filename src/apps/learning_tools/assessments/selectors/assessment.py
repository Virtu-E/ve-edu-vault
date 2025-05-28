import logging
from uuid import UUID

from asgiref.sync import sync_to_async

from src.utils.mixins.question_mixin import QuestionSetResources

from ..models import UserAssessmentAttempt

logger = logging.getLogger(__name__)


class AssessmentSelector:
    """Selector for retrieving assessment-related data"""

    def __init__(self, resource_context: QuestionSetResources):
        """
        Initialize the selector with resource context.

        Args:
            resource_context: Context containing user and learning objective
        """
        self.resource_context = resource_context

    async def get_assessment_id(self) -> UUID:
        """
        Get the assessment ID for the current context.

        Retrieves or creates an assessment attempt for the user and learning objective
        from the resource context.

        Returns:
            UUID: The assessment ID for the user's attempt

        """
        logger.debug(
            f"Getting assessment for user={self.resource_context.resources.user.id}, objective={self.resource_context.resources.learning_objective.id}"
        )
        attempt, _ = await sync_to_async(UserAssessmentAttempt.get_or_create_attempt)(
            self.resource_context.resources.user,
            self.resource_context.resources.learning_objective,
        )
        logger.debug(f"Assessment ID: {attempt.assessment_id}")
        return attempt.assessment_id
