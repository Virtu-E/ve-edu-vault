"""
ai_core.performance.performance_stats
~~~~~~~~~~~~~

This module contains the code that's responsible for calculating
the users score statistics on a sub_topic i.e failed difficulties,
passed difficulties
"""

import logging
from abc import ABC

from ai_core.learning_mode_rules import LearningModeType
from ai_core.performance.metrics.metrics_aggregator import MetricsCalculator
from course_ware.models import UserQuestionAttempts
from data_types.course_ware_schema import (QuestionMetadata,
                                           UserQuestionAttemptsSchema)
from exceptions import DatabaseQueryError

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
    """
    Base class for performance statistics.
    """

    def __call__(self) -> PerformanceStatsData:
        """
        Gets the users performance statistics on a sub_topic.

        Returns:
            PerformanceStatsData: The user performance statistics
        """
        raise NotImplementedError("The Performance Stats must be callable")


class PerformanceStats(PerformanceStatsBase):
    """
    Responsible for aggregating user performance statistics.
    """

    __slots__ = ("_sub_topic_id", "_user_id", "_metrics_aggregator")

    def __init__(
        self,
        sub_topic_id: int,
        user_id: int,
        metrics_aggregator: MetricsCalculator,
    ):
        """
        Initialize the PerformanceEngine instance.

        Args:
            sub_topic_id (str): The ID of the sub_topic for which the statistics
            should be calculated.
            user_id (int): The ID of the user for whom the statistics are being calculated.
            metrics_aggregator (StatisticsCalculatorInterface): An instance
            responsible for aggregating user performance statistics.
        """

        self._sub_topic_id = sub_topic_id
        self._user_id = user_id
        self._metrics_aggregator = metrics_aggregator

    def __call__(self) -> PerformanceStatsData:
        """
        Gets the users performance statistics on a topic

        Returns:
           PerformanceStatsData: The user performance statistics
        """
        return self._get_sub_topic_performance_stats()

    def _get_sub_topic_performance_stats(self) -> PerformanceStatsData:
        """
        Calculate and retrieve the user's performance statistics for the specified sub_topic.

        Returns:
            PerformanceStatsData: Contains performance metrics such a
            s ranked_difficulties and difficulty_status.

        If no question attempts are available for the sub_topic,
        the method returns an empty PerformanceStats object.
        """
        question_attempts = self._get_user_attempt_question_attempt_instance()
        if not question_attempts:
            log.info(
                "No question attempts found for sub_topic %s and for user %s",
                self._sub_topic_id,
                self._user_id,
            )
            return PerformanceStatsData(
                ranked_difficulties=[], difficulty_completion={}, difficulty_scores={}
            )

        question_metadata_current_version = (
            question_attempts.get_latest_question_metadata
        )
        return self._metrics_aggregator.aggregate_metrics(
            {
                key: QuestionMetadata(**value)
                for key, value in question_metadata_current_version.items()
            }
        )

    def _get_user_attempt_question_attempt_instance(
        self,
    ) -> UserQuestionAttempts:
        """
        Retrieve the user's question attempt data for the specified sub_topic.

        Returns:
            UserQuestionAttempts | None: The user's question attempt
             instance, or None if no data is found.

        Raises:
            DatabaseQueryError: Raised if an unexpected error
            occurs while querying the database.
        """
        try:
            question_attempt_instance = UserQuestionAttempts.objects.get(
                user_id=self._user_id, sub_topic_id=self._sub_topic_id
            )
            UserQuestionAttemptsSchema.model_validate(question_attempt_instance)
            return question_attempt_instance
        except UserQuestionAttempts.DoesNotExist as exc:
            log.error(
                "No question attempts found for user_id= %s, sub_topic_id= %s.",
                self._user_id,
                self._sub_topic_id,
            )
            raise UserAttemptsNotFoundError(self._user_id, self._sub_topic_id) from exc
        except Exception as e:
            log.error(
                "Error retrieving question metadata for user_id= %s, sub_topic_id=%s",
                self._user_id,
                self._sub_topic_id,
            )
            raise DatabaseQueryError("An unexpected error occurred") from e

    @classmethod
    def create_performance_stats(
        cls, user_id: int, sub_topic_id: int, learning_mode: LearningModeType
    ) -> "PerformanceStats":
        """
        Factory method to create a new PerformanceStats instance.

        Args:
            user_id (int): The ID of the user for whom the performance engine is created.
            sub_topic_id (int): The ID of the sub_topic for which performance is being calculated.
            learning_mode (LearningModeType): The learning mode to determine the type
            of performance calculator.

        Returns:
            PerformanceStats: The created PerformanceStats instance.
        """
        # TODO : required correct questions should be dynamic
        metrics_aggregator = MetricsCalculator(required_correct_questions=0)
        return cls(
            user_id=user_id,
            sub_topic_id=sub_topic_id,
            metrics_aggregator=metrics_aggregator,
        )

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._sub_topic_id}, {self._user_id},"
            f" {self._metrics_aggregator})"
        )

    def __str__(self) -> str:
        """Return a user-friendly string representation of the performance statistics."""
        return (
            f"Performance Stats for User {self._user_id} on Topic {self._sub_topic_id}"
        )
