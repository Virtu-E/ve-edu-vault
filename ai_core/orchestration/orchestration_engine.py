import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from decouple import config

from ai_core.ai.edu_ai_engine import EduAIEngine
from ai_core.ai.prompt_generators.base_prompt_generator import (
    BaseQuestionPromptGenerator,
)
from ai_core.ai.prompt_generators.lang_chain_prompt_generator import (
    LangChainQuestionPromptGenerator,
)
from ai_core.contextual_analyzer.context_builder import QuestionContextBuilder
from ai_core.contextual_analyzer.context_engine import ContextEngine
from ai_core.contextual_analyzer.stats.stats_calculator import (
    create_difficulty_stats_calculator,
)
from ai_core.learning_mode_rules import BaseLearningModeRule, LearningModeType
from course_ware.models import Category, Course, Topic
from data_types.ai_core import PerformanceStats, QuestionPromptGeneratorConfig
from data_types.course_ware_schema import QuestionMetadata
from exceptions import OrchestrationError, ValidationError
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface
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
        self.context_engine_initialized = False
        self.ai_engine_initialized = False

    def all_initialized(self) -> bool:
        return all(
            [
                self.context_engine_initialized,
                self.ai_engine_initialized,
            ]
        )


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
        block_id: str,
        user_id: int,
        question_metadata: dict[str, QuestionMetadata | Any],
        question_set_ids: set[str],
        course_id: int,
        topic_id: int,
        category_id: int,
        learning_mode: LearningModeType,
        learning_mode_rule: BaseLearningModeRule,
        performance_stats: PerformanceStats,
        database_engine: NoSqLDatabaseEngineInterface,
    ):
        self._block_id = block_id
        self._user_id = user_id
        self._question_metadata = question_metadata
        self._learning_mode = learning_mode
        self._learning_mode_rule = learning_mode_rule
        self._question_set_ids = question_set_ids
        self._performance_stats = performance_stats
        self._course = Course.objects.get(id=course_id)
        self._category = Category.objects.get(id=category_id)
        self._topic = Topic.objects.get(id=topic_id)
        self._config = OrchestrationConfig(
            database_name=config("NO_SQL_DATABASE_NAME"),
            learning_history_collection=config("LEARNING_HISTORY_COLLECTION_NAME"),
        )
        self._database_engine = database_engine

        # Initialize state tracker
        self._state = EngineState()

        # Initialize components as None
        self._context_engine = None
        self._ai_engine = None
        self._prompt_generator = None
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
            self._logger.info(
                f"Starting initialization for user {self._user_id} and topic {self._block_id}"
            )

            # Initialize context engine
            self._context_engine = self._create_context_engine()
            self._learning_history = (
                self._context_engine.generate_learning_history_context()
            )
            self._state.context_engine_initialized = True

            # Initialize AI engine last
            self._ai_engine = self._create_ai_engine(
                performance_stats=self._performance_stats
            )
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
            self._logger.info(f"Starting question processing for user {self._user_id }")
            return {
                "learning_history": self._learning_history.model_dump(),
                "ai_recommendations": self._ai_engine.get_ai_recommendation(),
            }

        except Exception as e:
            self._logger.error(f"Failed to process question: {str(e)}")
            raise OrchestrationError(f"Question processing failed: {str(e)}")

    def cleanup(self) -> None:
        """Cleanup any resources used by the engine"""
        # TODO : to be implemented
        pass

    def _create_mongo_question_repository(self) -> MongoQuestionRepository:
        """Creates and caches MongoDB question repository instance"""
        return MongoQuestionRepository(
            database_engine=self._database_engine,
            database_name=self._config.database_name,
            collection_name=self._course.course_key,
            validator=MongoQuestionValidator(),
        )

    def _create_learning_history_repository(self) -> MongoLearningHistoryRepository:
        """Creates and caches learning history repository instance"""
        return MongoLearningHistoryRepository(
            database_engine=self._database_engine,
            database_name=self._config.database_name,
            collection_name=self._config.learning_history_collection,
        )

    def _create_context_builder(self) -> QuestionContextBuilder:
        return QuestionContextBuilder(
            question_repository=self._create_mongo_question_repository()
        )

    def _create_context_engine(self) -> ContextEngine:
        """Creates context engine with all required dependencies"""
        return ContextEngine(
            user_id=self._user_id,
            block_id=self._block_id,
            question_metadata=self._question_metadata,
            question_set_ids=self._question_set_ids,
            learning_history_repository=self._create_learning_history_repository(),
            context_builder=self._create_context_builder(),
            stats_calculator=create_difficulty_stats_calculator(),
            learning_mode=self._learning_mode.value,
        )

    def _create_prompt_repository(self) -> MongoQuestionBankRepository:
        return MongoQuestionBankRepository(
            database_engine=self._database_engine,
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
            question_ids=list(self._question_set_ids),
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
