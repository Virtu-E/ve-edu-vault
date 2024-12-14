from data_types.questions import Question
from mongodb import mongo_database
from nosql_database_engine import NoSqLDatabaseEngineInterface


class RecommendationEngine:
    """
    Responsible for recommending a users question set given his/her performance on prior questions.
    """

    # due to the nature of questions, we will be sorely using no sql databases to store the questions, hence the no sql database interface
    def __init__(
        self,
        performance_engine,
        database_engine: NoSqLDatabaseEngineInterface,
        database_name: str,
        collection_name: str,
    ):
        self._performance_engine = performance_engine
        self._database_engine = database_engine
        self._database_name = database_name
        self._collection_name = collection_name

    """
    Fetches a list of questions from the specified database collection.

    Args:
        category: e.g : quadratic_equations
        topic: e.g : completing the square.
        examination_level: e.g : MSCE.
        academic_class: e.g. : Form 3
        difficulty: e.g. : hard

    Returns:
        A list of `Question` objects matching the specified criteria.

    Raises:
        (Specify any potential exceptions, e.g., `DatabaseConnectionError`, `DocumentNotFoundError`)
    """

    # TODO : handle database error connections gracefully
    def get_questions_list_from_database(
        self,
        category: str,
        topic: str,
        examination_level: str,
        academic_class: str,
        difficulty: str,
    ) -> list[Question]:
        collection = self._database_engine.fetch_from_db(
            self._collection_name, self._database_name
        )
        query = {
            "category": category,
            "topic": topic,
            "examination_level": examination_level,
            "academic_class": academic_class,
            "difficulty": difficulty,
        }
        return collection.find(query)
