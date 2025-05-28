from typing import List
import logging
from uuid import UUID

from src.apps.learning_tools.assessments.selectors.assessment import AssessmentSelector
from src.repository.graded_responses.data_types import GradedResponse
from src.repository.graded_responses.providers.response_provider import GradingResponseProvider
from src.repository.question_repository.exceptions import QuestionAttemptError
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


class GradedResponseService:
    """A service class responsible for retrieving and saving graded responses for users."""

    def __init__(
        self,
        resource_context: QuestionSetResources,
        grading_response_provider: GradingResponseProvider,
    ):
        """
        Initialize the GradedResponseService with injected dependencies.

        Args:
            resource_context: Context containing user and learning objective information
            grading_response_provider: Provider for fetching and saving grading responses
        """
        self.resource_context = resource_context
        self.user_id = resource_context.resources.user.id
        self.collection_name = resource_context.resources.collection_name
        self.grading_response_provider = grading_response_provider

    async def get_graded_responses(self, assessment_id: UUID) -> List[GradedResponse]:
        """
        Retrieve all graded responses for the configured user and learning objective.

        Args:
            assessment_id: The assessment ID to retrieve graded responses for

        Returns:
            List[GradedResponse]: List of graded responses for the user

        Raises:
            QuestionAttemptError: If retrieval fails due to provider issues,
                                assessment selection errors, or other system failures
        """
        logger.debug(
            "Getting graded responses for user %s, collection %s, assessment %s",
            self.user_id,
            self.collection_name,
            assessment_id,
        )

        graded_responses = await self.grading_response_provider.get_grading_responses(
            user_id=self.user_id,
            collection_name=self.collection_name,
            assessment_id=assessment_id,
        )

        logger.info(
            "Retrieved %d graded responses for user %s, assessment %s",
            len(graded_responses),
            self.user_id,
            assessment_id,
        )

        return graded_responses

    async def save_graded_response(
        self, graded_response: GradedResponse, assessment_id: UUID
    ) -> None:
        """
        Save a graded response to the database.

        Args:
            graded_response: The graded response to save
            assessment_id: The assessment ID to associate with the graded response

        Raises:
            QuestionAttemptError: If saving the graded response fails
        """
        try:
            await self.grading_response_provider.save_grading_response(
                user_id=self.user_id,
                question_id=graded_response.question_id,
                assessment_id=assessment_id,
                grading_response=graded_response,
            )

            logger.info(
                "Saved graded response for user %s, question %s, assessment %s",
                self.user_id,
                graded_response.question_id,
                assessment_id,
            )

        except Exception as e:
            logger.error(
                f"Failed to save graded response for user {self.user_id}, "
                f"question {graded_response.question_id}, assessment {assessment_id}: {e}"
            )
            raise QuestionAttemptError(
                f"Failed to save graded response for question {graded_response.question_id}"
            ) from e

    @classmethod
    def get_service(
        cls,
        resource_context: QuestionSetResources,
    ) -> "GradedResponseService":
        """
        Factory method to create a GradedResponseService instance with default providers.

        Args:
            resource_context: Context containing user and learning objective information

        Returns:
            GradedResponseService: Configured service instance
        """
        grading_response_provider = GradingResponseProvider.get_mongo_provider(
            collection_name=resource_context.resources.collection_name
        )
        return cls(
            resource_context=resource_context,
            grading_response_provider=grading_response_provider,
        )


async def get_graded_responses(
        *, resource_context: QuestionSetResources,) -> List[GradedResponse]:
    selector = AssessmentSelector(resource_context=    resource_context)
    assessment_id = await  selector.get_assessment_id()
    graded_response_service = GradedResponseService.get_service(resource_context=resource_context)
    question_attempts = await graded_response_service.get_graded_responses(assessment_id=assessment_id)
    return question_attempts
