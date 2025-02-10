from abc import ABC, abstractmethod

from data_types.ai_core import EvaluationResult


class LearningHistoryRepository(ABC):
    """Interface Segregation - Separate database operations"""

    @abstractmethod
    def save_learning_history(
        self, user_id: str, block_id: str, evaluation_result: EvaluationResult
    ) -> None:
        pass


class MongoLearningHistoryRepository(LearningHistoryRepository):
    """Concrete implementation of learning history repository"""

    def __init__(self, mongo_engine, database_name: str, collection_name: str):
        self.mongo_engine = mongo_engine
        self.database_name = database_name
        self.collection_name = collection_name

    def save_learning_history(
        self, user_id: str, topic_id: str, evaluation_result: EvaluationResult
    ) -> None:
        learning_history_data = {
            "user_id": user_id,
            "topic_id": topic_id,
            "result": evaluation_result.passed,
            "next_mode": evaluation_result.next_mode,
            "performance_stats": evaluation_result.performance_stats,
        }

        self.mongo_engine.write_to_db(
            data=learning_history_data,
            collection_name=self.collection_name,
            database_name=self.database_name,
            timestamp=True,
        )
