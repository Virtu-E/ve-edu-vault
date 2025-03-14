from abc import ABC, abstractmethod
from typing import List

from bson import ObjectId

from data_types.questions import Question
from exceptions import QuestionFetchError
from repository.databases.no_sql_database import NoSqLDatabaseEngineInterface


class QuestionRepositoryMixin(ABC):
    """Repository interface for question-related operations"""

    @abstractmethod
    def get_questions_by_ids(self, question_ids: List[str]) -> List[Question]:
        """Retrieve questions by their IDs"""
        pass


class QuestionValidator(ABC):
    @abstractmethod
    def validate_ids(self, question_ids: List[str]) -> List[ObjectId]:
        pass


class MongoQuestionValidator(QuestionValidator):
    def validate_ids(self, question_ids: List[str]) -> List[ObjectId]:
        object_ids = [ObjectId(id) for id in question_ids if ObjectId.is_valid(id)]
        if not object_ids:
            raise QuestionFetchError("No valid question IDs found")
        return object_ids
