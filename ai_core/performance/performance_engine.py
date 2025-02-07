import logging
from abc import ABC, abstractmethod

from ai_core.learning_mode_rules import LearningModeType
from ai_core.performance.calculators.base_calculator import (
    PerformanceCalculatorInterface,
)
from ai_core.performance.calculators.calculator_factory import (
    PerformanceCalculatorFactory,
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
    Responsible for calculating the user's performance on a topic.
    """

    def __init__(
        self,
        topic_id: int,
        user_id: int,
        performance_calculator: PerformanceCalculatorInterface,
    ):
        """
        Initialize the PerformanceEngine instance.

        Args:
            topic_id (str): The ID of the topic for which performance is being calculated.
            user_id (int): The ID of the user for whom performance is being calculated.
            performance_calculator (PerformanceCalculatorInterface): An instance responsible for calculating performance metrics.
        """

        self.topic_id = topic_id
        self.user_id = user_id
        self.performance_calculator = performance_calculator

    def get_topic_performance_stats(self) -> PerformanceStats:
        """
        Calculate and retrieve the user's performance statistics for the specified topic.

        Returns:
            PerformanceStats: Contains performance metrics such as ranked_difficulties and difficulty_status.

        If no question attempts are available for the topic, the method returns an empty PerformanceStats object.
        """
        question_attempt_instance = self._get_user_attempt_question_attempt_instance()

        if not question_attempt_instance:
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

    def _get_user_attempt_question_attempt_instance(
        self,
    ) -> UserQuestionAttempts | None:
        """
        Retrieve the user's question attempt data for the specified topic.

        Returns:
            UserQuestionAttempts | None: The user's question attempt instance, or None if no data is found.

        Raises:
            DatabaseQueryError: Raised if an unexpected error occurs while querying the database.
        """
        try:
            question_attempt_instance = UserQuestionAttempts.objects.get(
                user_id=self.user_id, topic_id=self.topic_id
            )
            UserQuestionAttemptsSchema.model_validate(question_attempt_instance)
            return question_attempt_instance
        except UserQuestionAttempts.DoesNotExist:
            log.info(
                f"No question attempts found for user_id={self.user_id}, topic_id={self.topic_id}."
            )
            return None
        except Exception as e:
            log.error(
                f"Error retrieving question metadata for user_id={self.user_id}, topic_id={self.topic_id}: {e}"
            )
            raise DatabaseQueryError(f"An unexpected error occurred: {e}")


def create_performance_engine(
    user_id: int, topic_id: int, learning_mode: LearningModeType
) -> PerformanceEngine:
    """
    Creates and initializes an instance of the PerformanceEngine.

    Args:
        user_id (int): The ID of the user for whom the performance engine is created.
        topic_id (int): The ID of the topic for which performance is being calculated.
        learning_mode (LearningModeType): The learning mode to determine the type of performance calculator.

    Returns:
        PerformanceEngine: An instance of the PerformanceEngine configured with the provided user, topic, and learning mode.
    """
    factory = PerformanceCalculatorFactory()
    return PerformanceEngine(
        user_id=user_id,
        topic_id=topic_id,
        performance_calculator=factory.create_calculator(learning_mode),
    )
