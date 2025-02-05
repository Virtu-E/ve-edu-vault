import logging
from typing import Dict
from dataclasses import dataclass

from django.db import transaction

from course_ware.models import UserQuestionAttempts, UserQuestionSet, EdxUser, Topic
from course_ware_ext.models import TopicMastery
from data_types.ai_core import PerformanceStats
from grade_book.messages import ModeMessageGenerator
from grade_book.performance_evaluator import PerformanceEvaluator
from grade_book.strategy import LearningModeStrategy
from repository.grade_book import LearningHistoryRepository

log = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Data class to hold evaluation results"""

    status: str
    passed: bool
    next_mode: str
    mode_guidance: str
    guidance: str
    performance_stats: PerformanceStats | None
    ai_recommendation: Dict


class Gradebook:
    def __init__(self, performance_evaluator: PerformanceEvaluator, message_generator: ModeMessageGenerator, learning_mode_strategy: LearningModeStrategy, learning_history_repository: LearningHistoryRepository, user_question_set: UserQuestionSet, topic: Topic, user: EdxUser, user_attempt: UserQuestionAttempts):
        self._performance_evaluator = performance_evaluator
        self._message_generator = message_generator
        self._learning_mode_strategy = learning_mode_strategy
        self._learning_history_repository = learning_history_repository
        self._user_question_set = user_question_set
        self._topic = topic
        self._user = user
        self._user_attempt = user_attempt

    def evaluate_performance(self, current_mode: str) -> EvaluationResult:
        """Evaluate user performance"""
        if current_mode == "mastered":
            return EvaluationResult(
                status="success",
                passed=True,
                next_mode="mastered",
                mode_guidance="You've mastered all difficulty levels! Practice with unlimited questions at any time.",
                performance_stats=None,
                guidance="Continue practicing to maintain mastery.",
                ai_recommendation={},
            )

        has_failed, ai_recommendations, performance_stats = self._performance_evaluator.evaluate().values()

        next_mode = self._learning_mode_strategy.get_next_mode(current_mode, has_failed)

        message = self._message_generator.get_message(current_mode, len(performance_stats.failed_difficulties))
        return EvaluationResult(
            status="success",
            passed=not has_failed,
            next_mode=next_mode,
            mode_guidance=message,
            performance_stats=performance_stats,
            guidance="Continue practicing to maintain mastery.",
            ai_recommendation=ai_recommendations,
        )

    def process_evaluation_side_effects(
        self,
        evaluation_result: EvaluationResult,
    ) -> None:
        """Process evaluation side effects atomically"""
        try:
            with transaction.atomic():
                # TODO : implement the save learning history logic
                # self._learning_history_repository.save_learning_history(self._user.id, self._topic.block_id, evaluation_result)
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
        self._user_attempt.current_learning_mode = EvaluationResult.next_mode
        self._user_attempt.question_metadata[next_version] = dict()
        self._user_attempt.question_metadata_description[next_version] = {
            "status": "Completed" if evaluation_result.passed else "Not Started",
            "learning_mode": evaluation_result.next_mode,
            "guidance": self._learning_mode_strategy.get_guidance_message(evaluation_result.next_mode),
            "mode_guidance": evaluation_result.mode_guidance,
        }

        self._user_attempt.current_learning_mode = evaluation_result.next_mode
        self._user_attempt.save()

    def _update_user_question_set(self) -> None:
        self._user_question_set.question_list_ids = [{}]
        # user_question_set.save()

    def _update_topic_mastery(self, evaluation_result: EvaluationResult) -> None:
        topic_mastery, _ = TopicMastery.objects.get_or_create(topic=self._topic, user=self._user)

        num_failed_difficulties = len(evaluation_result.performance_stats.failed_difficulties)
        total_difficulties = 3
        points_per_difficulty = 100 // total_difficulties  # Each difficulty level is worth 33 points
        if evaluation_result.passed and num_failed_difficulties == 0:
            topic_mastery.points_earned = 100
            topic_mastery.mastery_status = "mastered"

        points_earned = (total_difficulties - num_failed_difficulties) * points_per_difficulty
        topic_mastery.points_earned = points_earned
        topic_mastery.mastery_status = "in_progress"
        topic_mastery.save()
