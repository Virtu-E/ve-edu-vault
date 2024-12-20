import json
import re
from typing import Any, Dict, List, Literal, Tuple

from performance_engine import PerformanceEngineInterface

from ai_core.utils import fetch_from_model
from course_ware.models import UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import RecommendationEngineConfig
from data_types.questions import Question
from exceptions import DatabaseQueryError, QuestionFetchError
from nosql_database_engine import NoSqLDatabaseEngineInterface


class UserDataError(Exception):
    """Base exception for user data operations"""

    pass


class RecommendationEngine:
    """
    Responsible for recommending a user's question set based on their performance on prior questions.

    This engine uses a combination of performance metrics and question metadata to generate
    personalized question recommendations for users.
    """

    def __init__(
        self,
        performance_engine: PerformanceEngineInterface,
        database_engine: NoSqLDatabaseEngineInterface,
        config: RecommendationEngineConfig,
    ):
        """
        Initialize the recommendation engine.

        Args:
            performance_engine: Engine for calculating user performance metrics
            database_engine: NoSQL database interface for question storage
            config: Configuration parameters for the recommendation engine
        """
        self.performance_engine = performance_engine
        self.database_engine = database_engine
        self.database_name = config.database_name
        self.collection_name = config.collection_name
        self.category = config.category
        self.topic = config.topic
        self.examination_level = config.examination_level
        self.academic_class = config.academic_class
        self.user_id = config.user_id
        self.topic_id = config.topic_id
        self.min_questions_threshold = 9  # Minimum number of questions to recommend

    def set_users_recommended_questions(self) -> None:
        """
        Sets the user's recommended questions in the database.

        This method handles both creating new records and updating existing ones.

        """

        # TODO : batch operations ?
        recommended_questions = self._get_users_recommended_questions()

        # Handle UserQuestionSet
        self._save_recommended_questions(recommended_questions)

        # Handle UserQuestionAttempts
        self._update_user_question_attempts()

    def _save_recommended_questions(
        self, recommended_questions: List[Question]
    ) -> None:

        users_question_table = fetch_from_model(
            UserQuestionSet, user_id=self.user_id, topic_id=self.topic_id
        )
        users_question_table.question_set_ids = json.dumps(
            [{"id": question._id} for question in recommended_questions]
        )
        users_question_table.save()

    def _update_user_question_attempts(self) -> None:

        user_question_attempts = fetch_from_model(
            UserQuestionAttempts, user_id=self.user_id, topic_id=self.topic_id
        )
        next_version = self.get_next_version(user_question_attempts.question_metadata)
        user_question_attempts.question_metadata[next_version] = {}
        user_question_attempts.save()

    def _get_questions_list_from_database(
        self,
        difficulty: str,
    ) -> List[Question]:
        """
        Fetches questions from the database based on specified criteria.

        Args:
            difficulty: The difficulty level of questions to fetch

        Returns:
            List of Question objects matching the criteria

        Raises:
            QuestionFetchError: If there's an error fetching questions from the database
        """
        try:
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
            documents = collection.find(query)
            return [Question(**doc) for doc in documents]
        except Exception as e:
            raise QuestionFetchError(
                f"Failed to fetch questions from database: {str(e)}"
            )

    def _get_question_ids(self) -> list[Dict[str]]:
        """
        Extracts all question IDs from the UserQuestionSet table

        Returns:
            A list containing a dictionary with question IDs
        """

        try:
            user_question_set = fetch_from_model(
                UserQuestionSet, user_id=self.user_id, topic_id=self.topic_id
            )
            return user_question_set.question_set_ids
        except Exception as e:
            raise DatabaseQueryError(f"Error processing question IDs: {str(e)}")

    def _exclude_current_users_questions(
        self, recommended_questions: List[Question]
    ) -> List[Question]:
        """
        Filters out questions that the user has already attempted.

        Args:
            recommended_questions: List of potentially recommended questions

        Returns:
            Filtered list of questions excluding those already attempted by the user
        """
        current_users_question_ids = self._get_question_ids()

        question_ids = {question["id"] for question in current_users_question_ids}

        filtered_questions = [
            question
            for question in recommended_questions
            if question["_id"] not in question_ids
        ]

        return filtered_questions

    def _process_ranked_difficulties(
        self,
        ranked_difficulties: List[Tuple[Literal["easy", "medium", "hard"], float]],
    ) -> List[Question]:
        """
        Processes ranked difficulties to fetch corresponding questions.

        Args:
            ranked_difficulties: List of tuples containing difficulty levels and their scores

        Returns:
            List of questions based on the ranked difficulties
        """
        recommended_questions: List[Question] = []
        for difficulty, _ in ranked_difficulties:
            questions = self._get_questions_list_from_database(difficulty)
            recommended_questions.extend(questions)
        return recommended_questions

    def _get_users_recommended_questions(self) -> List[Question]:
        """
        Generates recommended questions based on user performance.

        Returns:
            List of recommended Question objects

        """

        ranked_difficulties, _ = self.performance_engine.get_topic_performance_stats()
        recommended_questions = self._process_ranked_difficulties(ranked_difficulties)
        filtered_questions = self._exclude_current_users_questions(
            recommended_questions
        )

        if len(filtered_questions) < self.min_questions_threshold:
            # TODO: Implement AI-based question recommendation
            raise QuestionFetchError(
                "Insufficient questions to recommend; consider AI-based generation."
            )

        return filtered_questions

    @staticmethod
    def get_next_version(versions: Dict[str, Any]) -> str:
        """
        Generates the next version number based on existing versions.

        Args:
            versions: Dictionary of existing versions

        Returns:
            Next version string in the format "vX.Y.Z"
        """
        if not versions:
            return "v0.0.0"

        try:
            version_keys = list(versions.keys())
            version_keys.sort(key=lambda x: [int(i) for i in x.lstrip("v").split(".")])

            latest_version = version_keys[-1]
            match = re.match(r"v(\d+)\.(\d+)\.(\d+)", latest_version)

            if match:
                major, _, _ = map(int, match.groups())
                return f"v{major + 1}.0.0"
            return "v0.0.0"
        except Exception:
            return "v0.0.0"
