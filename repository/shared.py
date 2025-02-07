from abc import ABC, abstractmethod
from typing import List

from bson import ObjectId

from data_types.questions import Question
from exceptions import QuestionFetchError
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface


class QuestionRepository(ABC):
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


class MongoQuestionRepository(QuestionRepository):
    def __init__(
        self,
        database_engine: NoSqLDatabaseEngineInterface,
        database_name: str,
        validator: QuestionValidator,
        collection_name: str,
    ):
        self.database_engine = database_engine
        self.database_name = database_name
        self.validator = validator
        self.collection_name = collection_name

    def get_questions_by_ids(self, question_ids: List[str]) -> List[Question]:
        object_ids = self.validator.validate_ids(question_ids)
        questions = self.database_engine.fetch_from_db(
            self.collection_name, self.database_name, {"_id": {"$in": object_ids}}
        )
        return [
            Question(**{**question, "_id": str(question["_id"])}).model_dump(
                by_alias=True, exclude={"choices": {"is_correct"}}
            )
            for question in questions
        ]
