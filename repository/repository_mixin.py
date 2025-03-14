from abc import ABC, abstractmethod
from typing import List

from data_types.ai_core import EvaluationResult

from .data_types import Question


class QuestionRepositoryMixin(ABC):
    """Mixin to add question related functionality"""

    @abstractmethod
    def get_questions_by_ids(self, question_ids: List[str], collection_name : str) -> List[Question]:
        """Retrieve questions by their IDs"""
        raise NotImplementedError("get_questions_by_ids is not implemented")

    @abstractmethod
    def get_question_by_single_id(self, question_id: str, collection_name:str) -> Question:
        """Retrieve question by ID"""
        raise NotImplementedError("get_question_by_single_id is not implemented")




class LearningHistoryRepositoryMixin(ABC):

    @abstractmethod
    def save_learning_history(
        self, user_id: str, block_id: str, evaluation_result: EvaluationResult
    ) -> None:
        raise NotImplementedError("save_learning_history is not implemented")

class QuestionAttemptRepositoryMixin(ABC):
    @abstractmethod
