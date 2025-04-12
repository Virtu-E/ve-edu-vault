import logging
from abc import ABC, abstractmethod
from typing import Any

from ai_core.contextual_analyzer.context_builder import \
    QuestionContextBuilderInterface
from ai_core.contextual_analyzer.stats.stats_calculator import \
    DifficultyStatsCalculatorInterface
from data_types.ai_core import LearningHistory, LearningMode, ModeData
from data_types.course_ware_schema import QuestionMetadata
from repository.ai_core.learning_history import LearningHistoryRepository

logger = logging.getLogger(__name__)


class ContextEngineInterface(ABC):
    @abstractmethod
    def generate_learning_history_context(self) -> LearningHistory:
        """Build the complete learning context for AI analysis"""
        raise NotImplementedError


class ContextEngine(ContextEngineInterface):
    """Primary context processor engine that coordinates the construction of learning history context for AI application."""

    def __init__(
        self,
        user_id: int,
        block_id: str,
        learning_mode: LearningMode,
        question_metadata: dict[str, QuestionMetadata | Any],
        question_set_ids: set[str],
        learning_history_repository: LearningHistoryRepository,
        context_builder: QuestionContextBuilderInterface,
        stats_calculator: DifficultyStatsCalculatorInterface,
    ):
        self._learning_history_repository = learning_history_repository
        self._context_builder = context_builder
        self._stats_calculator = stats_calculator
        self._learning_mode = learning_mode
        self._user_id = user_id
        self._block_id = block_id
        self._question_metadata = question_metadata
        self._question_set_ids = question_set_ids

    def generate_learning_history_context(self) -> LearningHistory:
        """Build the complete learning context for AI analysis"""
        try:
            learning_history = self._learning_history_repository.get_learning_history(
                self._user_id, self._block_id
            )

            question_contexts = self._context_builder.build_question_context(
                list(self._question_set_ids), self._question_metadata
            )

            # Calculate difficulty stats
            difficulty_stats = {}
            for difficulty in set(q.difficulty for q in question_contexts):
                difficulty_stats[difficulty] = self._stats_calculator.calculate(
                    question_contexts, difficulty
                )

            # Create and update mode data
            mode_data = ModeData(
                questions=question_contexts, difficultyStats=difficulty_stats
            )

            learning_history.modeHistory.setdefault(self._learning_mode, []).append(
                mode_data
            )

            # Save updated history
            # TODO : should not do this here
            self._learning_history_repository.save_learning_history(learning_history)

            return learning_history

        except Exception as e:
            logger.error(f"Error building learning context: {str(e)}")
            raise
