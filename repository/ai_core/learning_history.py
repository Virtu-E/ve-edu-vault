from abc import abstractmethod, ABC
from typing import Optional

from data_types.ai_core import LearningHistory
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface


class LearningHistoryRepository(ABC):
    """Repository interface for learning history operations"""

    @abstractmethod
    def get_learning_history(self, user_id: str, block_id: str) -> Optional[LearningHistory]:
        """Retrieve learning history for a user and block"""
        pass

    @abstractmethod
    def save_learning_history(self, learning_history: LearningHistory) -> None:
        """Save learning history"""
        pass


class MongoLearningHistoryRepository(LearningHistoryRepository):
    def __init__(
        self,
        database_engine: NoSqLDatabaseEngineInterface,
        database_name: str,
        collection_name: str,
    ):
        self.database_engine = database_engine
        self.database_name = database_name
        self.collection_name = collection_name

    def get_learning_history(self, user_id: str, block_id: str) -> LearningHistory:
        query = {"userId": user_id, "block_id": block_id}
        history = self.database_engine.fetch_one_from_db(self.collection_name, self.database_name, query)
        if not history:
            return LearningHistory(userId=user_id, block_id=block_id, modeHistory={})

    def save_learning_history(self, learning_history: LearningHistory) -> None:
        # TODO : implement this
        pass
        # self.database_engine.insert_into_db(self.collection_name, self.database_name, learning_history.model_dump())
