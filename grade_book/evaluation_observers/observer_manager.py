import asyncio
from typing import List

from django.db import transaction

from ai_core.performance.data_types import PerformanceStatsData
from course_ware.models import EdxUser, SubTopic, UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import EvaluationResult
from grade_book.evaluation_observers.base_observer import EvaluationObserver
from grade_book.evaluation_observers.database_observers import (
    LearningHistoryObserver,
    TopicMasteryObserver,
    UserAttemptObserver,
    UserQuestionSetObserver,
)


class EvaluationObserverRegistry:
    """Registry of evaluation observers"""

    def __init__(self):
        self._observers: List[EvaluationObserver] = []

    def register_observer(self, observer: EvaluationObserver) -> None:
        """Register a new observer"""
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister_observer(self, observer: EvaluationObserver) -> None:
        """Unregister an existing observer"""
        if observer in self._observers:
            self._observers.remove(observer)

    async def notify_observers(self, evaluation_result: EvaluationResult) -> None:
        """Notify all registered observers about an evaluation result"""
        await asyncio.gather(
            *(observer.process_async(evaluation_result) for observer in self._observers)
        )


class PerformanceStats:
    pass


class EvaluationSideEffectManager:
    """Coordinates the processing of all side effects for an evaluation result"""

    def __init__(
        self,
        user_attempt: UserQuestionAttempts,
        user_question_set: UserQuestionSet,
        sub_topic: SubTopic,
        user: EdxUser,
        performance_stats: PerformanceStatsData,
    ):
        self._registry = EvaluationObserverRegistry()
        self._setup_observers(
            user_attempt, user_question_set, sub_topic, user, performance_stats
        )

    def _setup_observers(
        self,
        user_attempt: UserQuestionAttempts,
        user_question_set: UserQuestionSet,
        sub_topic: SubTopic,
        user: EdxUser,
        performance_stats: PerformanceStatsData,
    ) -> None:
        """Set up the default observers"""
        # Register all standard observers
        self._user_question_set = user_question_set
        self._registry.register_observer(UserAttemptObserver(user_attempt))
        self._registry.register_observer(UserQuestionSetObserver(user_question_set))
        self._registry.register_observer(
            TopicMasteryObserver(sub_topic, user, performance_stats)
        )
        self._registry.register_observer(LearningHistoryObserver(user, sub_topic))

    def register_additional_observer(self, observer: EvaluationObserver) -> None:
        """Register an additional observer"""
        self._registry.register_observer(observer)

    async def process_side_effects(self, evaluation_result: EvaluationResult) -> None:
        """Process all side effects atomically"""
        # TODO : might be potential gotcha in the future. If the observers get complex
        # lets say we add an API observer that errors, but we still need to process
        async with transaction.atomic():
            await self._registry.notify_observers(evaluation_result)

        # Exit out of Grading mode
        self._user_question_set.grading_mode = False
        self._user_question_set.save()
