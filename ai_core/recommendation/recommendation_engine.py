import asyncio
import json
import logging
from functools import lru_cache
from typing import List, Literal, Set, TypeVar

from ai_core.performance.performance_engine import PerformanceEngineInterface
from ai_core.utils import fetch_from_model
from course_ware.models import UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import (
    RecommendationEngineConfig,
    RecommendationQuestionMetadata,
)
from data_types.questions import Question
from exceptions import (
    DatabaseQueryError,
    DatabaseUpdateError,
    InsufficientQuestionsError,
    QuestionFetchError,
)
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface

# Type variables for generics
T = TypeVar("T")

log = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Responsible for recommending questions based on user performance.

    This engine uses performance metrics and question metadata to generate
    personalized question recommendations for users.
    """

    def __init__(
        self,
        performance_engine: PerformanceEngineInterface,
        database_engine: NoSqLDatabaseEngineInterface,
        config: RecommendationEngineConfig,
        question_threshold: int,
    ):
        """
        Initialize the recommendation engine.

        Args:
            performance_engine: Engine for calculating user performance metrics
            database_engine: NoSQL database interface
            config: Configuration parameters
            question_threshold: Threshold for question recommendations
        """
        self.performance_engine = performance_engine
        self.database_engine = database_engine
        self.config = config
        self.question_threshold = question_threshold

        # Initialize database attributes
        self._init_database_attributes()

    def _init_database_attributes(self) -> None:
        """Initialize attributes from config"""
        self.database_name = self.config.database_name
        self.collection_name = self.config.collection_name
        self.metadata = RecommendationQuestionMetadata(
            category=self.config.category,
            topic=self.config.topic,
            examination_level=self.config.examination_level,
            academic_class=self.config.academic_class,
            difficulty=None,  # this will be set after we have decided what
            # level of recommended questions we want to recommend to the user
        )

    @property
    def user_id(self) -> int:
        """Get user ID from config"""
        return self.config.user_id

    @property
    def topic_id(self) -> int:
        """Get topic ID from config"""
        return self.config.topic_id

    async def set_users_recommended_questions(self) -> None:
        """
        Sets the user's recommended questions in the database.
        Handles both creating new records and updating existing ones.
        """
        try:
            recommended_questions = await self._get_users_recommended_questions()

            await self._save_recommended_questions(recommended_questions)
            await self._update_user_question_attempts()

            log.info(f"Successfully updated questions for user {self.user_id}")

        except Exception as e:
            log.error(f"Error setting recommended questions: {str(e)}")
            raise DatabaseUpdateError(f"Error setting recommended questions: {str(e)}")

    async def _save_recommended_questions(self, recommended_questions: List[Question]) -> None:
        """Save recommended questions to the database"""
        question_set = await fetch_from_model(UserQuestionSet, user_id=self.user_id, topic_id=self.topic_id)
        # question_list_ids is a JSON field
        question_set.question_list_ids = json.dumps(self._serialize_questions(recommended_questions))
        await question_set.save()

    async def _update_user_question_attempts(self) -> None:
        """Update user question attempts with new version"""
        attempts = await fetch_from_model(UserQuestionAttempts, user_id=self.user_id, topic_id=self.topic_id)
        next_version = attempts.get_next_version
        attempts.question_metadata[next_version] = dict()
        await attempts.save()

    @lru_cache(maxsize=128)
    async def _get_questions_list_from_database(self, difficulty: str) -> List[Question]:
        """
        Fetches questions from the database based on Recommendation Question Metadata.
        Uses caching to improve performance for repeated requests.

        Args:
            difficulty: The difficulty level of questions to fetch

        Returns:
            List of Question objects matching the criteria

        Raises:
            QuestionFetchError: If there's an error fetching questions
        """
        try:
            documents = await self.database_engine.fetch_from_db(
                self.collection_name,
                self.database_name,
                query=self._build_query(difficulty).__dict__,
            )
            return [Question(**doc) for doc in documents]

        except Exception as e:
            log.error(f"Database fetch error: {str(e)}")
            raise QuestionFetchError(f"Failed to fetch questions: {str(e)}")

    def _build_query(self, difficulty: str) -> RecommendationQuestionMetadata:
        """Build the database query based on metadata"""
        return self.metadata.model_copy(update={"difficulty": difficulty})

    async def _get_question_ids(self) -> Set[str]:
        """
        Extracts question IDs from the UserQuestionSet table

        Returns:
            Set of question IDs
        """
        try:
            question_set = await fetch_from_model(UserQuestionSet, user_id=self.user_id, topic_id=self.topic_id)
            return question_set.get_question_set_ids

        except Exception as e:
            log.error(f"Error fetching question IDs: {str(e)}")
            raise DatabaseQueryError(f"Error processing question IDs: {str(e)}")

    @staticmethod
    def _exclude_current_users_questions(recommended_questions: List[Question], current_ids: Set[str]) -> List[Question]:
        """
        Filters out questions that the user has already attempted.

        Args:
            recommended_questions: List of potentially recommended questions
            current_ids: Set of current question IDs

        Returns:
            Filtered list of questions excluding those already attempted
        """
        return [q for q in recommended_questions if q.question_id not in current_ids]

    async def _process_ranked_difficulties(
        self,
        ranked_difficulties: list[tuple[Literal["easy", "medium", "hard"], float]],
    ) -> List[Question]:
        """
        Processes ranked difficulties to fetch corresponding questions.

        Args:
            ranked_difficulties: List of tuples containing difficulty levels and scores

        Returns:
            List of questions based on the ranked difficulties
        """
        tasks = [self._get_questions_list_from_database(difficulty) for difficulty, _ in ranked_difficulties]
        question_lists = await asyncio.gather(*tasks)
        return [q for sublist in question_lists for q in sublist]

    async def _get_users_recommended_questions(self) -> List[Question]:
        """
        Generates recommended questions based on user performance.

        Returns:
            List of recommended Question objects

        Raises:
            InsufficientQuestionsError: If not enough questions are available
        """
        (
            ranked_difficulties,
            stats,
        ) = await self.performance_engine.get_topic_performance_stats()
        recommended_questions = await self._process_ranked_difficulties(ranked_difficulties)

        current_ids = await self._get_question_ids()
        filtered_questions = self._exclude_current_users_questions(recommended_questions, current_ids)

        if len(filtered_questions) < self.question_threshold:
            log.warning(f"Insufficient questions for user {self.user_id}")
            raise InsufficientQuestionsError("Insufficient questions available. Consider AI-based generation.")

        return filtered_questions

    @staticmethod
    def _serialize_questions(questions: List[Question]) -> List[dict[str, str]]:
        """Serialize questions to a compatible format for the User QuestionSet table"""
        return [{"id": q.question_id} for q in questions]
