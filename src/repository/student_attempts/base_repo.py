from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from src.repository.student_attempts.data_types import StudentQuestionAttempt


class AbstractAttemptRepository(ABC):
    @abstractmethod
    async def save_attempt(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        update: Dict[str, Any],
        collection_name: str,
    ) -> bool:
        """
        Save a single student's question attempt to the database.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            assessment_id: UUID of the assessment
            update: Dictionary containing attempt data to save
            collection_name: Database collection name

        Returns:
            True if save was successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_question_attempt_single(
        self,
        user_id: str,
        question_id: str,
        collection_name: str,
        assessment_id: UUID,
    ) -> Optional[StudentQuestionAttempt]:
        """
        Retrieve a specific student's question attempt.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            collection_name: Database collection name
            assessment_id: UUID of the assessment

        Returns:
            StudentQuestionAttempt if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_question_attempts_by_aggregation(
        self, collection_name: str, pipeline: Any
    ) -> List[StudentQuestionAttempt]:
        """
        Retrieve multiple question attempts using aggregation pipeline.

        Args:
            collection_name: Database collection name
            pipeline: Aggregation pipeline for filtering/grouping

        Returns:
            List of StudentQuestionAttempt objects
        """
        pass

    @abstractmethod
    async def save_bulk_attempt(
        self,
        collection_name: str,
        data: Union[Dict, list],
    ) -> bool:
        """
        Save multiple attempts to the database in bulk operation.

        Args:
            collection_name: Database collection name
            data: Dictionary or list containing multiple attempt records

        Returns:
            True if bulk save was successful, False otherwise
        """
        pass
