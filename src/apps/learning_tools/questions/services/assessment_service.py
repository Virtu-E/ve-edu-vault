import logging
from typing import Optional
from uuid import UUID

from src.apps.learning_tools.assessments.util import get_assessment_id
from src.utils.mixins.question_mixin import QuestionSetResources

from ..exceptions import QuestionAttemptError
from .data_types import AssessmentContext

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service for handling assessment-related operations"""

    def __init__(self, timeout_seconds: Optional[int] = None):
        self.timeout_seconds = timeout_seconds

    @staticmethod
    async def get_assessment_id(resource_context: QuestionSetResources) -> UUID:
        """
        Get the assessment ID for the current context.

        Args:
            resource_context: Context containing user and learning objective

        Returns:
            UUID: The assessment ID

        Raises:
            QuestionAttemptError: If assessment ID cannot be retrieved
        """
        try:
            assessment_id = await get_assessment_id(
                user=resource_context.resources.user,
                learning_objective=resource_context.resources.learning_objective,
            )
            logger.debug(
                "Retrieved assessment ID %s for user %s",
                assessment_id,
                resource_context.resources.user.id,
            )
            return assessment_id

        except Exception as e:
            logger.error(f"Failed to get assessment ID: {e}")
            raise QuestionAttemptError("Failed to retrieve assessment ID") from e

    @staticmethod
    async def validate_assessment_context(context: AssessmentContext) -> bool:
        """
        Validate that the assessment context is valid.

        Args:
            context: Assessment context to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not context.user_id:
                logger.warning("Invalid assessment context: missing user_id")
                return False
            if not context.question_id:
                logger.warning("Invalid assessment context: missing question_id")
                return False
            if not context.collection_name:
                logger.warning("Invalid assessment context: missing collection_name")
                return False

            logger.debug("Assessment context validation passed")
            return True

        except Exception as e:
            logger.error(f"Error validating assessment context: {e}")
            return False
