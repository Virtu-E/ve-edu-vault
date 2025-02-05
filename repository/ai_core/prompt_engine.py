from abc import ABC, abstractmethod
from typing import List

from data_types.ai_core import QuestionBank
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface
from repository.shared import QuestionValidator


class PromptEngineRepositoryInterface(ABC):
    @abstractmethod
    def get_question_bank(self, question_ids: List[str]) -> list[QuestionBank]:
        raise not NotImplementedError


class MongoQuestionBankRepository(PromptEngineRepositoryInterface):
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

    def get_question_bank(self, question_ids: List[str]) -> list[QuestionBank]:
        object_ids = self.validator.validate_ids(question_ids)

        questions = self.database_engine.fetch_from_db(self.collection_name, self.database_name, {"_id": {"$in": object_ids}})
        return [QuestionBank(**{**question, "_id": str(question["_id"])}).model_dump(by_alias=True) for question in questions]
