"""
ai_core.performance.performance_stats
~~~~~~~~~~~~~

This module contains the code that's responsible for calculating
the user's score statistics on a sub_topic i.e failed difficulties,
passed difficulties
"""

import logging
from abc import ABC

from ai_core.performance.metrics.metrics_aggregator import MetricsAggregator
from course_ware.models import UserQuestionAttempts
from data_types.course_ware_schema import QuestionMetadata

from .data_types import PerformanceStatsData

log = logging.getLogger(__name__)


class UserAttemptsNotFoundError(Exception):
    """Exception raised when no question attempts are found for a user on a particular sub_topic."""

    def __init__(self, user_id: int, sub_topic_id: int):
        self.user_id = user_id
        self.sub_topic_id = sub_topic_id
        self.message = f"No question attempts found for user_id={user_id}, topic_id={sub_topic_id}."
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class PerformanceStatsBase(ABC):
    """Base class for performance statistics."""

    def __call__(self) -> PerformanceStatsData:
        """
        Gets the user's performance statistics on a sub_topic.

        Returns:
            PerformanceStatsData: The user performance statistics
        """
        raise NotImplementedError("The Performance Stats must be callable")


class PerformanceStatsEngine(PerformanceStatsBase):
    """Responsible for aggregating user performance statistics."""

    __slots__ = ("_user_question_attempts", "_metrics_aggregator")

    def __init__(
        self,
        user_question_attempts: UserQuestionAttempts,
        metrics_aggregator: MetricsAggregator,
    ):
        """
        Initialize the PerformanceStatsEngine instance.

        Args:
            user_question_attempts: The user question attempts to analyze
            metrics_aggregator: An instance responsible for aggregating user performance statistics
        """
        self._user_question_attempts = user_question_attempts
        self._metrics_aggregator = metrics_aggregator

    def __call__(self) -> PerformanceStatsData:
        """
        Gets the user's performance statistics on a topic.

        Returns:
            PerformanceStatsData: The user performance statistics
        """
        return self._get_sub_topic_performance_stats()

    def _get_sub_topic_performance_stats(self) -> PerformanceStatsData:
        """
        Calculate and retrieve the user's performance statistics for the specified sub_topic.

        Returns:
            PerformanceStatsData: Contains performance metrics such as ranked_difficulties
            and difficulty_status.
        """
        question_metadata_current_version = (
            self._user_question_attempts.get_latest_question_metadata
        )
        return self._metrics_aggregator.aggregate_metrics(
            {
                key: QuestionMetadata(**value)
                for key, value in question_metadata_current_version.items()
            }
        )

    @classmethod
    def create_performance_stats(
        cls,
        user_question_attempts: UserQuestionAttempts,
        required_correct_questions: int,
    ) -> "PerformanceStatsEngine":
        """
        Factory method to create a new PerformanceStatsEngine instance.

        Args:
            user_question_attempts: The user question attempts to analyze
            required_correct_questions: Number of correct questions required

        Returns:
            PerformanceStatsEngine: The created PerformanceStatsEngine instance
        """
        metrics_aggregator = MetricsAggregator.create_aggregator_with_defaults(
            required_correct_questions
        )
        return cls(
            user_question_attempts=user_question_attempts,
            metrics_aggregator=metrics_aggregator,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._user_question_attempts},"
            f" {self._metrics_aggregator})"
        )

    def __str__(self) -> str:
        """Return a user-friendly string representation of the performance statistics."""
        return "Performance Stats for User"
