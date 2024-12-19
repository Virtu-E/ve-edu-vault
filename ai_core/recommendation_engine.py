from typing import Literal

from performance_engine import PerformanceEngineInterface

from data_types.ai_core import RecommendationEngineConfig
from data_types.questions import Question
from nosql_database_engine import NoSqLDatabaseEngineInterface


class RecommendationEngine:
    """
    Responsible for recommending a users question set given his/her performance on prior questions.
    """

    # due to the nature of questions, we will be sorely using no sql databases to store the questions, hence the no sql database interface
    def __init__(
        self,
        performance_engine: PerformanceEngineInterface,
        database_engine: NoSqLDatabaseEngineInterface,
        config: RecommendationEngineConfig,
    ):
        self.performance_engine = performance_engine
        self.database_engine = database_engine
        self.database_name = config.database_name
        self.collection_name = config.collection_name
        self.category = config.category
        self.topic = config.topic
        self.examination_level = config.examination_level
        self.academic_class = config.academic_class

    """
    Fetches a list of questions from the specified database collection.

    Args:
        performance_engine : the engine that will be used for performance calculations
        database_engine : no sql database engine that will be used.
        config : configuration object of type RecommendationEngineConfig

    Returns:
        A list of `Question` objects matching the specified criteria.

    Raises:
        (Specify any potential exceptions, e.g., `DatabaseConnectionError`, `DocumentNotFoundError`)
    """

    # TODO : handle database error connections gracefully
    def _get_questions_list_from_database(
        self,
        difficulty: str,
    ) -> list[Question]:
        collection = self.database_engine.fetch_from_db(
            self.collection_name, self.database_name
        )
        query = {
            "category": self.category,
            "topic": self.topic,
            "examination_level": self.examination_level,
            "academic_class": self.academic_class,
            "difficulty": difficulty,
        }
        return collection.find(query)

    def _get_questions_id_to_exclude(self, questions: list[str]) -> list[str]:
        pass

    def _process_incomplete_ranked_question_difficulties(
        self,
        incomplete_ranked_difficulties: list[
            tuple[Literal["easy", "medium", "hard"], float]
        ],
    ) -> list[str]:
        pass

    def get_users_recommended_questions(self):
        """
        Returns a list of Question IDs based on the users performance on prior questions.

        """
        incomplete_ranked_difficulties, difficulty_status = (
            self.performance_engine.get_topic_performance_stats()
        )
