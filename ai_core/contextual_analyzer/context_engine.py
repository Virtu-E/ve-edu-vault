import logging
from abc import ABC, abstractmethod

from ai_core.contextual_analyzer.context_builder import QuestionContextBuilderInterface
from ai_core.contextual_analyzer.stats.stats_calculator import DifficultyStatsCalculatorInterface
from course_ware.models import EdxUser, Topic, UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import LearningHistory, ModeData
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
        user: EdxUser,
        topic: Topic,
        user_question_attempt: UserQuestionAttempts,
        user_question_set: UserQuestionSet,
        learning_history_repository: LearningHistoryRepository,
        context_builder: QuestionContextBuilderInterface,
        stats_calculator: DifficultyStatsCalculatorInterface,
    ):
        self.user = user
        self.topic = topic
        self.user_question_attempt = user_question_attempt
        self.user_question_set = user_question_set
        self.learning_history_repository = learning_history_repository
        self.context_builder = context_builder
        self.stats_calculator = stats_calculator

    def generate_learning_history_context(self) -> LearningHistory:
        """Build the complete learning context for AI analysis"""
        try:
            learning_mode = self.user_question_attempt.current_learning_mode

            learning_history = self.learning_history_repository.get_learning_history(self.user.id, self.topic.block_id)

            question_contexts = self.context_builder.build_question_context(
                list(self.user_question_set.get_question_set_ids),
                self.user_question_attempt.get_latest_question_metadata,
            )

            # Calculate difficulty stats
            difficulty_stats = {}
            for difficulty in set(q.difficulty for q in question_contexts):
                difficulty_stats[difficulty] = self.stats_calculator.calculate(question_contexts, difficulty)

            # Create and update mode data
            mode_data = ModeData(questions=question_contexts, difficultyStats=difficulty_stats)

            learning_history.modeHistory.setdefault(learning_mode, []).append(mode_data)

            # Save updated history
            # TODO : should not do this here
            self.learning_history_repository.save_learning_history(learning_history)

            return learning_history

        except Exception as e:
            logger.error(f"Error building learning context: {str(e)}")
            raise
