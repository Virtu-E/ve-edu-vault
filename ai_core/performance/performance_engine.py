import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Union

from ai_core.performance.calculators.performance_calculators import (
    PerformanceCalculatorInterface,
)
from course_ware.models import UserQuestionAttempts
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata, UserQuestionAttemptsSchema
from exceptions import DatabaseQueryError

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
        question_attempt_data, question_attempt_instance = (
            self._get_user_attempt_question_metadata()
        )

        if not question_attempt_data and not question_attempt_instance:
            log.info("No question attempt data for topic {}".format(self.topic_id))
            return PerformanceStats(ranked_difficulties=[], difficulty_status={})
        question_metadata_current_version = (
            question_attempt_instance.get_latest_question_metadata
        )
        return self.performance_calculator.calculate_performance(
            {
                key: QuestionMetadata(**value)
                for key, value in question_metadata_current_version.items()
            }
        )

    def _get_user_attempt_question_metadata(
        self,
    ) -> Union[
        Tuple[Dict[str, Dict[str, "QuestionMetadata"]], "UserQuestionAttempts"],
        Tuple[Dict, None],
    ]:
        """
        Retrieve user's question attempt data.

        Returns:
            Tuple:
                - A dictionary containing question metadata and the question attempt instance.
                - An empty dictionary and None if no data is found.

        Raises:
            DatabaseQueryError: If an unexpected error occurs.
        """
        try:
            question_attempt_instance = UserQuestionAttempts.objects.get(
                user_id=self.user_id, topic_id=self.topic_id
            )
            schema = UserQuestionAttemptsSchema.model_validate(
                question_attempt_instance
            )
            return schema.question_metadata, question_attempt_instance
        except UserQuestionAttempts.DoesNotExist:
            log.info(
                f"No question attempts found for user_id={self.user_id}, topic_id={self.topic_id}."
            )
            return {}, None
        except Exception as e:
            log.error(
                f"Error retrieving question metadata for user_id={self.user_id}, topic_id={self.topic_id}: {e}"
            )
            raise DatabaseQueryError(f"An unexpected error occurred: {e}")
