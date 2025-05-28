from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.repository.graded_responses.data_types import GradedResponse


class AbstractGradingResponseRepository(ABC):
    @abstractmethod
    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        response: GradedResponse,
        collection_name: str,
    ) -> bool:
        """
        Save a grading response to the database.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            assessment_id: UUID of the assessment
            response: GradedResponse object containing grading results
            collection_name: Database collection name

        Returns:
            True if save was successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_grading_responses(
        self,
        user_id: str,
        assessment_id: UUID,
        collection_name: str,
    ) -> List[GradedResponse]:
        """
        Retrieve all grading responses for a user and assessment.

        Args:
            user_id: Unique identifier for the student
            assessment_id: UUID of the assessment
            collection_name: Database collection name

        Returns:
            List of GradedResponse objects
        """
        pass
