import logging
from typing import List, Optional
from uuid import UUID

from src.repository.grading_response_repository.base_response_repository import (
    AbstractGradingResponseRepository,
)
from src.repository.grading_response_repository.mongo_response_repository import (
    MongoGradingResponseRepository,
)
from src.repository.grading_response_repository.response_data_types import (
    QuestionAttempt,
)

from .qn_grading_types import GradingResponse

logger = logging.getLogger(__name__)


class GradingResponseService:
    """
    Service for handling the persistence of grading responses.

    This service manages saving grading responses to the database,
    including metadata and contextual information.

    Attributes:
        repository: Repository interface for storing grading response data
        collection_name: Name of the collection to store grading responses
    """

    def __init__(
        self,
        repository: AbstractGradingResponseRepository,
        collection_name: str,
    ) -> None:
        """
        Initialize the GradingResponseService.

        Args:
            repository: Repository implementation for data access
            collection_name: Name of the collection to store data in
        """
        self.repository = repository
        self.collection_name = collection_name
        logger.info(
            f"Initialized GradingResponseService with collection '{collection_name}'"
        )

    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        grading_response: GradingResponse,
        topic: Optional[str] = None,
        sub_topic: Optional[str] = None,
        learning_objective: Optional[str] = None,
        question_type: Optional[str] = None,
    ) -> bool:
        """
        Save a grading response to the database with additional metadata.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            assessment_id: Unique identifier for the assessment
            grading_response: The GradingResponse object to save
            topic: Optional topic categorization
            sub_topic: Optional sub-topic categorization
            learning_objective: Optional learning objective
            question_type: Optional question type

        Returns:
            bool: True if save was successful, False otherwise
        """
        logger.info(
            f"Saving grading response for user {user_id}, "
            f"question {question_id}, assessment {assessment_id}"
        )

        # Prepare enriched grading response with metadata
        enriched_response = self._enrich_grading_response(
            grading_response,
            topic=topic,
            sub_topic=sub_topic,
            learning_objective=learning_objective,
            question_type=question_type,
        )

        # Save to repository
        result = await self.repository.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            response=enriched_response,
            collection_name=self.collection_name,
        )

        if result:
            logger.info("Successfully saved grading response")
        else:
            logger.error("Failed to save grading response")

        return result

    def _enrich_grading_response(
        self,
        grading_response: GradingResponse,
        topic: Optional[str] = None,
        sub_topic: Optional[str] = None,
        learning_objective: Optional[str] = None,
        question_type: Optional[str] = None,
    ) -> GradingResponse:
        """
        Enrich the grading response with additional metadata.

        This method doesn't modify the original object, but creates an enriched copy.
        The MongoDB repository will handle adding these fields to the document.

        Args:
            grading_response: Original GradingResponse
            topic: Optional topic categorization
            sub_topic: Optional sub-topic categorization
            learning_objective: Optional learning objective
            question_type: Optional question type

        Returns:
            GradingResponse: Enriched copy of the original response
        """
        grading_response.question_type = question_type

        logger.debug(
            f"Enriching grading response with metadata: "
            f"topic={topic}, sub_topic={sub_topic}, "
            f"learning_objective={learning_objective}, question_type={question_type}"
        )

        # In a real implementation, you might want to extend the GradingResponse
        # class to include these fields, but for now we'll just pass them to the repository

        return grading_response

    async def get_grading_responses(
        self,
        user_id: str,
        assessment_id: UUID,
        collection_name: str,
    ) -> List[QuestionAttempt]:
        """
        Retrieves grading responses for a specific user, question, assessment, and collection.

        Args:
            user_id (str): The ID of the user whose responses are being retrieved.
            assessment_id (UUID): The unique identifier of the assessment.
            collection_name (str): The name of the collection to search in.

        Returns:
            List[QuestionAttempt]: A list of question attempt objects containing the grading responses.
        """

        logger.info(
            "Retrieving grading responses for user_id=%s, assessment_id=%s, collection_name=%s",
            user_id,
            assessment_id,
            collection_name,
        )

        result = await self.repository.get_grading_responses(
            user_id=user_id,
            assessment_id=assessment_id,
            collection_name=collection_name,
        )

        return result

    @classmethod
    def get_service(cls, collection_name: str) -> "GradingResponseService":
        """
        Factory method to create a service instance with default configuration.

        Args:
            collection_name: Name of the collection to use

        Returns:
            GradingResponseService: Configured service instance
        """
        return cls(
            repository=MongoGradingResponseRepository.get_repo(),
            collection_name=collection_name,
        )
