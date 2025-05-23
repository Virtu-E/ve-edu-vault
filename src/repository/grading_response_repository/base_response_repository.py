from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.library.grade_book_v2.question_grading.data_types import GradingResponse
from src.repository.grading_response_repository.response_data_types import (
    GradedResponse,
)


class AbstractGradingResponseRepository(ABC):
    @abstractmethod
    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        response: GradingResponse,
        collection_name: str,
    ) -> bool:
        """Save an attempt to the database"""
        pass

    @abstractmethod
    async def get_grading_responses(
        self,
        user_id: str,
        assessment_id: UUID,
        collection_name: str,
    ) -> List[GradedResponse]:
        """Save an attempt to the database"""
        pass
