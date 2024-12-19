import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Union

from ai_core.performance_calculators import PerformanceCalculatorInterface
from course_ware.models import UserQuestionAttempts
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata, UserQuestionAttemptsSchema

log = logging.getLogger(__name__)


class PerformanceEngineInterface(ABC):
    @abstractmethod
    def get_topic_performance_stats(self) -> PerformanceStats:
        """
        Abstract method to get user's performance on a topic.

        Returns:
            PerformanceStats: Performance statistics including ranked_difficulties and difficulty_status
        """
        raise NotImplementedError


class PerformanceEngine(PerformanceEngineInterface):
    """
    Responsible for calculating the user's performance on a topic.'
    """

    def __init__(
        self,
        topic_id: str,
        user_id: int,
        performance_calculator: PerformanceCalculatorInterface,
    ):
        """
        Initialize the PerformanceEngine instance.

        Args:

            topic_id: Topic ID associated with the topic ( Topic Database Instance )
            user_id: User ID
            performance_calculator: Calculator instance for performance metrics
        """

        self.topic_id = topic_id
        self.user_id = user_id
        self.performance_calculator = performance_calculator

    def get_topic_performance_stats(self) -> PerformanceStats:
        """
        Main method to get user performance stats based on question attempts related to a topic.

        Returns:
            PerformanceStats containing performance metrics
        """
        question_attempt_data = self._get_user_attempt_question_metadata()
        if not question_attempt_data:
            return PerformanceStats(ranked_difficulties=[], difficulty_status={})
        question_metadata_current_version = self._get_current_question_version(
            question_attempt_data, self._parse_version
        )
        return self.performance_calculator.calculate_performance(
            question_metadata_current_version
        )

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

    def _get_current_question_version(
        self,
        question_metadata: dict[str, dict[str, QuestionMetadata]],
        parse_version: Callable[[str], tuple],
    ) -> dict[str, QuestionMetadata]:
        """
        Get the current (latest) question version from metadata.

        Args:
            question_metadata: Nested dictionary containing versioned question metadata
            parse_version: Function to parse version strings

        Returns:
            Dictionary containing the question metadata with the latest version
        """

        try:
            latest_version = max(question_metadata.keys(), key=parse_version)
            return question_metadata[latest_version]
        except (ValueError, KeyError) as e:
            raise ValueError("Invalid version format in metadata") from e

    def _get_user_attempt_question_metadata(
        self,
    ) -> Union[dict[str, dict[str, QuestionMetadata]], {}]:
        """
        Retrieve user's question attempt data.

        Returns:
            Dictionary containing question metadata or empty dictionary

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
            log.info(f"UserQuestionAttempts.DoesNotExist for topic {self.topic_id}")
            return {}
        except Exception as e:
            log.error(f"An error occurred while retrieving question metadata: {e}")
            return {}
