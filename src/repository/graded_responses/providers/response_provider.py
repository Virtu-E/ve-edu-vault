import logging
from typing import List
from uuid import UUID

from src.repository.graded_responses.base_repo import AbstractGradingResponseRepository
from src.repository.graded_responses.data_types import GradedResponse
from src.repository.graded_responses.mongo.response_repository import (
    MongoGradingResponseRepository,
)

logger = logging.getLogger(__name__)


class GradingResponseProvider:
    """
    Provider for handling the persistence of grading responses.

    This manages saving grading responses to the database,
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
        Initialize the GradingResponseProvider.

        Args:
            repository: Repository implementation for data access
            collection_name: Name of the collection to store data in
        """
        self.repository = repository
        self.collection_name = collection_name
        logger.info(
            f"Initialized GradingResponseProvider with collection '{collection_name}'"
        )

    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        grading_response: GradedResponse,
    ) -> bool:
        """
        Save a grading response to the database with additional metadata.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            assessment_id: Unique identifier for the assessment
            grading_response: The GradingResponse object to save

        Returns:
            bool: True if save was successful, False otherwise
        """
        logger.info(
            f"Saving grading response for user {user_id}, "
            f"question {question_id}, assessment {assessment_id}"
        )

        result = await self.repository.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            response=grading_response,
            collection_name=self.collection_name,
        )

        if result:
            logger.info("Successfully saved grading response")
        else:
            logger.error("Failed to save grading response")

        return result

    async def get_grading_responses(
        self,
        user_id: str,
        assessment_id: UUID,
        collection_name: str,
    ) -> List[GradedResponse]:
        """
        Retrieve grading responses for a specific user and assessment.

        Args:
            user_id (str): The ID of the user whose responses are being retrieved
            assessment_id (UUID): The unique identifier of the assessment
            collection_name (str): The name of the collection to search in

        Returns:
            List[GradedResponse]: A list of graded response objects
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
    def get_mongo_provider(cls, collection_name: str) -> "GradingResponseProvider":
        """
        Factory method to create a provider instance with mongo.

        Args:
            collection_name: Name of the collection to use

        Returns:
            GradingResponseProvider: Configured provider instance
        """
        return cls(
            repository=MongoGradingResponseRepository.get_repo(),
            collection_name=collection_name,
        )
