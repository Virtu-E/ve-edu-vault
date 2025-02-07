import logging

from django.db import transaction

from course_ware.models import EdxUser, Topic, UserQuestionAttempts, UserQuestionSet
from course_ware_ext.models import TopicMastery
from data_types.ai_core import EvaluationResult, PerformanceStats
from grade_book.strategy import LearningModeStrategy

log = logging.getLogger(__name__)


class Gradebook:
    def __init__(
        self,
        learning_mode_strategy: LearningModeStrategy,
        user_question_set: UserQuestionSet,
        topic: Topic,
        user: EdxUser,
        user_attempt: UserQuestionAttempts,
        performance_stats: PerformanceStats,
    ):
        self._learning_mode_strategy = learning_mode_strategy
        self._user_question_set = user_question_set
        self._topic = topic
        self._user = user
        self._user_attempt = user_attempt
        self.performance_stats = performance_stats

    def evaluate_performance(self) -> EvaluationResult:
        """Evaluate user performance"""

        has_failed = any(
            status == "incomplete"
            for status in self.performance_stats.difficulty_status.values()
        )

        return EvaluationResult(
            status="success",
            passed=not has_failed,
            next_mode=self._learning_mode_strategy.get_next_mode(),
            previous_mode=self._learning_mode_strategy.get_previous_mode(),
        )

    def process_evaluation_side_effects(
        self,
        evaluation_result: EvaluationResult,
    ) -> None:
        """Process evaluation side effects atomically"""
        try:
            with transaction.atomic():
                # TODO : implement the save learning history logic
                # self._update_user_attempt(evaluation_result)
                # self._update_topic_mastery(evaluation_result)
                # self._update_user_question_set()
                pass

        except Exception as e:
            log.error(f"Failed to process evaluation side effects: {str(e)}")
            raise ValueError(f"Failed to process evaluation side effects: {str(e)}")

    def _update_user_attempt(self, evaluation_result: EvaluationResult) -> None:
        """Helper method to update user attempt"""
        next_version = self._user_attempt.get_next_version
        self._user_attempt.current_learning_mode = evaluation_result.next_mode.mode_name
        self._user_attempt.question_metadata[next_version] = dict()
        self._user_attempt.question_metadata_description[next_version] = {
            "status": "Completed" if evaluation_result.passed else "Not Started",
            "learning_mode": evaluation_result.next_mode.mode_name,
            "guidance": evaluation_result.next_mode.guidance,
            "mode_guidance": evaluation_result.next_mode.mode_guidance,
        }

        self._user_attempt.current_learning_mode = evaluation_result.next_mode
        self._user_attempt.save()

    def _update_user_question_set(self) -> None:
        # The next question set for the user will come from AI recommendation, which happens later down the line
        # TODO : make sure that the function that assigns the base question set to the user questions set does not fire
        self._user_question_set.question_list_ids = [{}]
        self._user_question_set.save()

    def _update_topic_mastery(self, evaluation_result: EvaluationResult) -> None:
        topic_mastery, _ = TopicMastery.objects.get_or_create(
            topic=self._topic, user=self._user
        )

        num_failed_difficulties = len(self.performance_stats.failed_difficulties)
        total_difficulties = 3
        points_per_difficulty = (
            100 // total_difficulties
        )  # Each difficulty level is worth 33 points
        if evaluation_result.passed and num_failed_difficulties == 0:
            topic_mastery.points_earned = 100
            topic_mastery.mastery_status = "mastered"

        points_earned = (
            total_difficulties - num_failed_difficulties
        ) * points_per_difficulty
        topic_mastery.points_earned = points_earned
        topic_mastery.mastery_status = "in_progress"
        topic_mastery.save()
