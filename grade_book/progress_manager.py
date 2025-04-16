from ai_core.performance.data_types import PerformanceStatsData
from course_ware.models import EdxUser, SubTopic, UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import EvaluationResult
from grade_book.learning_context import LearningModeContext

from .evaluation_observers.base_observer import EvaluationObserver
from .evaluation_observers.observer_manager import EvaluationSideEffectManager
from .tasks import run_side_effects_in_background


class LearningProgressManager:
    """Overall manager for evaluation and side effect processing"""

    def __init__(
        self,
        user_attempt: UserQuestionAttempts,
        user_question_set: UserQuestionSet,
        sub_topic: SubTopic,
        user: EdxUser,
        performance_stats: PerformanceStatsData,
    ):
        self._user_attempt = user_attempt
        self._performance_stats = performance_stats
        self._side_effect_manager = EvaluationSideEffectManager(
            user_attempt, user_question_set, sub_topic, user, performance_stats
        )
        self._user_question_set = user_question_set
        self._sub_topic_id = sub_topic.id
        self._user_id = user.id

    def register_additional_side_effect(self, observer: EvaluationObserver) -> None:
        """Register an additional side effect observer"""
        self._side_effect_manager.register_additional_observer(observer)

    def evaluate_and_process(self) -> EvaluationResult:
        """Evaluate user performance and process all side effects"""
        # First evaluate performance

        learning_context = LearningModeContext(
            self._performance_stats, self._user_attempt.current_learning_mode
        )

        has_failed = len(self._performance_stats.failed_difficulties) > 0

        # TODO : maybe i can return this evaluation result while processing the side effects
        evaluation_result = EvaluationResult(
            status="success",
            passed=not has_failed,
            next_mode=learning_context.get_next_mode(),
            previous_mode=learning_context.get_previous_mode(),
        )
        # The user is already in grading mode. Maybe waiting for side effects evaluation to finish
        # in the meantime, we can just show them the results
        if self._user_question_set.grading_mode:
            return evaluation_result

        self._user_question_set.grading_mode = True
        self._user_question_set.save()

        run_side_effects_in_background.delay(
            user_attempt_id=self._user_attempt.id,
            user_question_set_id=self._user_question_set.id,
            sub_topic_id=self._sub_topic_id,
            user_id=self._user_id,
            perf_stats_dict=self._performance_stats,
            eval_result_dict=evaluation_result.model_dump(),
        )

        return evaluation_result
