import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List

from decouple import config

from ai_core.ai.edu_ai_engine import EduAIEngine
from ai_core.ai.prompt_generators.base_prompt_generator import BaseQuestionPromptGenerator
from ai_core.ai.prompt_generators.lang_chain_prompt_generator import LangChainQuestionPromptGenerator
from ai_core.contextual_analyzer.context_builder import QuestionContextBuilder
from ai_core.contextual_analyzer.context_engine import ContextEngine
from ai_core.contextual_analyzer.stats.stats_calculator import create_difficulty_stats_calculator
from ai_core.learning_mode_rules import BaseLearningModeRule, LearningModeType
from ai_core.performance.calculators.base_calculator import PerformanceCalculatorInterface
from ai_core.performance.calculators.calculator_factory import PerformanceCalculatorFactory
from ai_core.performance.performance_engine import PerformanceEngine, PerformanceEngineInterface
from ai_core.validator.validator_engine import ValidationEngine
from course_ware.models import Category, Course, EdxUser, Topic, UserQuestionAttempts, UserQuestionSet
from data_types.ai_core import QuestionPromptGeneratorConfig
from exceptions import OrchestrationError, ValidationError
from no_sql_database.mongodb import mongo_database
from repository.ai_core.learning_history import MongoLearningHistoryRepository
from repository.ai_core.prompt_engine import MongoQuestionBankRepository
from repository.shared import MongoQuestionRepository, MongoQuestionValidator

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Configuration for the orchestration engine"""

    database_name: str
    learning_history_collection: str
    enable_caching: bool = True
    cache_size: int = 128
    validation_timeout: int = 30  # seconds


class EngineState:
    """Tracks the initialization state of different components"""

    def __init__(self):
        self.validator_initialized = False
        self.performance_engine_initialized = False
        self.context_engine_initialized = False
        self.ai_engine_initialized = False

    def all_initialized(self) -> bool:
        return all([
            self.validator_initialized,
            self.performance_engine_initialized,
            self.context_engine_initialized,
            self.ai_engine_initialized,
        ])


class OrchestrationEngineInterface(ABC):
    @abstractmethod
    def process_question(self) -> Dict:
        # TODO : document the return value properly
        raise NotImplementedError


class OrchestrationEngine(OrchestrationEngineInterface):
    """
    Enhanced orchestration engine that manages dependencies between different components
    and handles repository interactions.
    """

    def __init__(
        self,
        topic: Topic,
        user: EdxUser,
        course: Course,
        category: Category,
        learning_mode: LearningModeType,
        user_question_set: UserQuestionSet,
        learning_mode_rule: BaseLearningModeRule,
        question_attempt: UserQuestionAttempts,
    ):
        self._topic = topic
        self._user = user
        self._category = category
        self._question_attempt = question_attempt
        self.learning_mode = learning_mode
        self._learning_mode_rule = learning_mode_rule
        self._course = course
        self._user_question_set = user_question_set
        self._config = OrchestrationConfig(
            database_name=config("NO_SQL_DATABASE_NAME"),
            learning_history_collection=config("LEARNING_HISTORY_COLLECTION_NAME"),
        )

        # Initialize state tracker
        self._state = EngineState()

        # Initialize components as None
        self._validator = None
        self._context_engine = None
        self._ai_engine = None
        self._performance_engine = None
        self._prompt_generator = None
        self._performance_stats = None
        self._learning_history = None

        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.initialize()

    @property
    def is_initialized(self) -> bool:
        """Check if all components are properly initialized"""
        return self._state.all_initialized()

    def initialize(
        self,
    ) -> None:
        """
        Initializes all components in the correct dependency order.

        Raises:
            OrchestrationError: If initialization fails
            ValidationError: If validation fails
            EngineInitializationError: If any engine fails to initialize
        """
        try:
            self._logger.info(f"Starting initialization for user {self._user.id} and topic {self._topic.id}")

            # Initialize validator first
            self._validator = self._create_validator()
            validation_result = self._validator.run_all_validators(
                question_set=self._user_question_set,
                user_question_attempt_instance=self._question_attempt,
            )
            self._state.validator_initialized = True

            if validation_result:
                raise ValidationError(f"Validation failed: {validation_result}")

            # Initialize performance engine
            self._performance_engine = self._create_performance_engine()
            self._performance_stats = self._performance_engine.get_topic_performance_stats()
            self._state.performance_engine_initialized = True

            # Initialize context engine
            self._context_engine = self._create_context_engine(
                user_question_attempt=self._question_attempt,
                user_question_set=self._user_question_set,
            )
            self._learning_history = self._context_engine.generate_learning_history_context()
            self._state.context_engine_initialized = True

            # Initialize AI engine last
            self._ai_engine = self._create_ai_engine(performance_stats=self._performance_stats)
            self._state.ai_engine_initialized = True

            self._logger.info("Successfully initialized all components")

        except ValidationError as ve:
            self._logger.error(f"Validation failed: {str(ve)}")
            raise
        except Exception as e:
            self._logger.error(f"Failed to initialize orchestration engine: {str(e)}")
            raise OrchestrationError(f"Initialization failed: {str(e)}")

    def process_question(self) -> Dict:
        if not self.is_initialized:
            raise OrchestrationError("Orchestration engine not properly initialized")

        try:
            self._logger.info(f"Starting question processing for user {self._user.id}")
            return {
                "learning_history": self._learning_history,
                "performance_stats": self._performance_stats,
                "ai_recommendations": self._ai_engine.get_ai_recommendation(),
            }

        except Exception as e:
            self._logger.error(f"Failed to process question: {str(e)}")
            raise OrchestrationError(f"Question processing failed: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup any resources used by the engine"""
        # TODO : to be implemented
        pass

    @staticmethod
    def _create_validator() -> ValidationEngine:
        """Creates validator engine instance"""
        return ValidationEngine()

    def _create_mongo_question_repository(self) -> MongoQuestionRepository:
        """Creates and caches MongoDB question repository instance"""
        return MongoQuestionRepository(
            database_engine=mongo_database,
            database_name=self._config.database_name,
            collection_name=self._course.course_key,
            validator=MongoQuestionValidator(),
        )

    def _create_learning_history_repository(self) -> MongoLearningHistoryRepository:
        """Creates and caches learning history repository instance"""
        return MongoLearningHistoryRepository(
            database_engine=mongo_database,
            database_name=self._config.database_name,
            collection_name=self._config.learning_history_collection,
        )

    def _create_context_builder(self) -> QuestionContextBuilder:
        return QuestionContextBuilder(question_repository=self._create_mongo_question_repository())

    def _create_context_engine(
        self,
        user_question_attempt: UserQuestionAttempts,
        user_question_set: UserQuestionSet,
    ) -> ContextEngine:
        """Creates context engine with all required dependencies"""
        return ContextEngine(
            user=self._user,
            topic=self._topic,
            user_question_attempt=user_question_attempt,
            user_question_set=user_question_set,
            learning_history_repository=self._create_learning_history_repository(),
            context_builder=self._create_context_builder(),
            stats_calculator=create_difficulty_stats_calculator(),
        )

    def _create_prompt_repository(self) -> MongoQuestionBankRepository:
        return MongoQuestionBankRepository(
            database_engine=mongo_database,
            database_name=config("NO_SQL_DATABASE_NAME"),
            collection_name=self._course.course_key,
            validator=MongoQuestionValidator(),
        )

    def _failed_difficulties(self) -> List[str]:
        return self._performance_stats.failed_difficulties

    def _create_base_prompt_config(self) -> QuestionPromptGeneratorConfig:
        return QuestionPromptGeneratorConfig(
            course_name=self._course.name,
            topic_name=self._topic.name,
            academic_level=self._category.academic_class.name,
            category=self._category.name,
            syllabus="",  # TODO : create a syllabus parser to be used with AI
        )

    def _create_base_prompt(self) -> BaseQuestionPromptGenerator:
        return BaseQuestionPromptGenerator(
            rule=self._learning_mode_rule,
            learning_history=self._learning_history,
            repository=self._create_prompt_repository(),
            question_ids=list(self._user_question_set.get_question_set_ids),
            config=self._create_base_prompt_config(),
            failed_difficulties=self._failed_difficulties(),
        )

    def _create_prompt_generator(
        self,
    ) -> LangChainQuestionPromptGenerator:
        """Creates prompt generator with required dependencies"""
        return LangChainQuestionPromptGenerator(
            base_prompt=self._create_base_prompt(),
        )

    def _create_ai_engine(self, performance_stats: dict) -> EduAIEngine:
        """Creates AI engine instance with dependencies"""
        return EduAIEngine(prompt_generator=self._create_prompt_generator())

    def _create_performance_calculator(self) -> PerformanceCalculatorInterface:
        """Creates performance calculator based on learning mode"""
        return PerformanceCalculatorFactory.create_calculator(self.learning_mode)

    def _create_performance_engine(self) -> PerformanceEngineInterface:
        """Creates performance engine with calculator"""
        return PerformanceEngine(
            user_id=self._user.id,
            topic_id=self._topic.id,
            performance_calculator=self._create_performance_calculator(),
        )
