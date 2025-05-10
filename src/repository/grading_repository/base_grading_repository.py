from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID

from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt


class AbstractGradingRepository(ABC):
    @abstractmethod
    async def save_attempt(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        update: Dict[str, Any],
        collection_name: str,
    ) -> bool:
        """Save an attempt to the database"""
        pass

    @abstractmethod
    async def get_question_attempt_single(
        self,
        user_id: str,
        question_id: str,
        collection_name: str,
        assessment_id: UUID,
    ) -> Optional[StudentQuestionAttempt]:
        """Get a specific/single student question attempt"""
        pass
