from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from ai_core.performance_calculators import PerformanceCalculatorInterface
from course_ware.models import UserQuestionAttempts
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata, UserQuestionAttemptsSchema


class PerformanceEngineInterface(ABC):
    @abstractmethod
    def get_topic_performance_stats(self) -> PerformanceStats:
        """
        Abstract method to get user's performance on a topic.

        Returns:
            PerformanceStats: Performance statistics including rankings and status
        """
        raise NotImplementedError


class PerformanceEngine(PerformanceEngineInterface):
    """
    Responsible for calculating the user's performance on a topic.'
    """

    def __init__(
        self,
        category: str,
        topic_id: str,
        course_id: str,
        user_id: int,
        performance_calculator: PerformanceCalculatorInterface,
    ):
        """
        Initialize the PerformanceEngine instance.

        Args:
            category: Category of performance calculation
            topic_id: Topic ID associated with the user
            course_id: Course ID
            user_id: User ID
            performance_calculator: Calculator instance for performance metrics
        """
        self.category = category
        self.topic_id = topic_id
        self.course_id = course_id
        self.user_id = user_id
        self.performance_calculator = performance_calculator

    @staticmethod
    def _parse_version(version: str) -> tuple:
        """
        Parse version string into tuple of integers.

        Args:
            version: Version string (e.g., 'v1.0.0')

        Returns:
            Tuple of integers representing version components
        """
        try:
            parts = version.lstrip("v").split(".")
            return tuple(map(int, parts))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid version format: {version}") from e

    def get_topic_performance_stats(self) -> PerformanceStats:
        """
        Get user performance stats based on question attempts.

        Returns:
            PerformanceStats containing performance metrics
        """
        question_attempt_data = self._get_user_attempt_question_metadata()
        current_version_data = self._get_current_question_version(
            question_attempt_data, self._parse_version
        )
        return self.performance_calculator.calculate_performance(current_version_data)

    def _get_current_question_version(
        self,
        question_metadata: dict[str, dict[str, QuestionMetadata | Any]],
        parse_version: Callable[[str], tuple],
    ) -> dict[str, QuestionMetadata | Any]:
        """
        Get the current (latest) question version from metadata.

        Args:
            question_metadata: Nested dictionary containing question metadata
            parse_version: Function to parse version strings

        Returns:
            Dictionary containing latest version's question metadata
        """
        if not question_metadata:
            return {}

        try:
            latest_version = max(question_metadata.keys(), key=parse_version)
            return question_metadata[latest_version]
        except (ValueError, KeyError) as e:
            raise ValueError("Invalid version format in metadata") from e

    def _get_user_attempt_question_metadata(
        self,
    ) -> dict[str, dict[str, QuestionMetadata | Any]]:
        """
        Retrieve user's question attempt data.

        Returns:
            Dictionary containing question metadata

        Raises:
            UserQuestionAttempts.DoesNotExist: If no data found
        """
        try:
            question_attempt_instance = UserQuestionAttempts.objects.get(
                user_id=self.user_id, topic_id=self.topic_id
            )
            schema = UserQuestionAttemptsSchema.model_validate(
                question_attempt_instance
            )
            return schema.question_metadata
        except UserQuestionAttempts.DoesNotExist:
            print(
                f"No question attempt data found for user {self.user_id} "
                f"and topic {self.topic_id}."
            )
            return {}
        except Exception as e:
            print(f"An error occurred while retrieving question metadata: {e}")
            return {}
