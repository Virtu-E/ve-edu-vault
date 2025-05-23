import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional

from src.library.grade_book_v2.question_grading.data_types import AttemptedAnswer
from src.repository.question_repository.mongo_qn_repository import (
    MongoQuestionRepository,
)
from src.utils.mixins.question_mixin import QuestionSetResources

from ..exceptions import GradingError, QuestionAttemptError, QuestionNotFoundError
from .assessment_service import AssessmentService
from .attempt_service import AttemptSavingService, QuestionAttemptService
from .data_types import (
    AssessmentContext,
    AttemptContext,
    GradingConfig,
    RecordQuestionAttemptResponse,
    ServiceDependencies,
)
from .grading_service import GraderFactory, GradingService
from .question_service import QuestionService

log = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


class AttemptRecorder(ABC):
    """Abstract interface for recording attempts"""

    @abstractmethod
    async def record_attempt(self) -> RecordQuestionAttemptResponse:
        pass


class QuestionAttemptRecorder(AttemptRecorder):
    """
    Coordinates the process of recording a question attempt by orchestrating
    the various services needed in the workflow.

    This improved version uses dependency injection and breaks down complex operations
    into smaller, focused methods for better maintainability and testability.
    """

    def __init__(
        self,
        dependencies: ServiceDependencies,
        resource_context: QuestionSetResources,
    ) -> None:
        """
        Initialize the recorder with grouped dependencies.

        Args:
            dependencies: Grouped service dependencies
            resource_context: Context containing validation data and resources
        """
        self._deps = dependencies
        self._context = resource_context
        self._config = GradingConfig()

        logger.debug(
            f"QuestionAttemptRecorder initialized for collection: {resource_context.resources.collection_name}"
        )

    async def record_attempt(self) -> RecordQuestionAttemptResponse:
        """
        Main entry point for recording a question attempt.


        Returns:
            RecordQuestionAttemptResponse: The result of the attempt

        Raises:
            QuestionAttemptError: If the attempt recording fails
        """

        context = AssessmentContext(
            user_id=self._context.resources.user.id,
            question_id=self._context.validated_data["question_id"],
            collection_name=self._context.resources.collection_name,
        )
        try:
            await self._validate_context(context)

            logger.info(
                "Processing attempt for question %s by user %s",
                context.question_id,
                context.user_id,
            )

            # Prepare the assessment context
            assessment_data = await self._prepare_assessment_data(context)

            # Grade the attempt
            grading_result = await self._grade_attempt(assessment_data)

            # Handle the result
            if grading_result.success:
                await self._handle_successful_attempt(assessment_data, grading_result)
                self._log_success(context.question_id, context.user_id)
                return RecordQuestionAttemptResponse.success_response(
                    context.question_id, grading_result
                )
            else:
                self._log_failure(context.question_id, grading_result.feedback.message)
                return RecordQuestionAttemptResponse.failure_response(
                    context.question_id, grading_result
                )

        except (GradingError, QuestionNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing attempt: {e}")
            raise QuestionAttemptError(
                f"Failed to record attempt for question {context.question_id}"
            ) from e

    async def _validate_context(self, context: AssessmentContext) -> None:
        """
        Validate the assessment context.

        Args:
            context: Assessment context to validate

        Raises:
            QuestionAttemptError: If context is invalid
        """
        if not await self._deps.assessment_service.validate_assessment_context(context):
            raise QuestionAttemptError("Invalid assessment context")

    async def _prepare_assessment_data(self, context: AssessmentContext) -> dict:
        """
        Prepare all the data needed for the assessment.

        Args:
            context: Basic assessment context

        Returns:
            Dictionary containing all prepared data

        Raises:
            QuestionNotFoundError: If question is not found
        """
        try:
            grader = self._deps.grader_factory.get_grader(context.collection_name)
            assessment_id = await self._deps.assessment_service.get_assessment_id(
                self._context
            )

            question, question_attempt = await asyncio.gather(
                self._deps.question_service.get_question_by_id(context.question_id),
                self._deps.question_attempt_service.get_question_attempt(
                    user_id=context.user_id,
                    question_id=context.question_id,
                    assessment_id=assessment_id,
                ),
            )

            if not question:
                raise QuestionNotFoundError(f"Question {context.question_id} not found")

            return {
                "grader": grader,
                "assessment_id": assessment_id,
                "question": question,
                "question_attempt": question_attempt,
                "user_id": context.user_id,
                "question_id": context.question_id,
                "collection_name": context.collection_name,
            }

        except QuestionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to prepare assessment data: {e}")
            raise QuestionAttemptError("Failed to prepare assessment data") from e

    async def _grade_attempt(self, assessment_data: dict):
        """
        Grade the question attempt.

        Args:
            assessment_data: Prepared assessment data

        Returns:
            GradingResponse: Result of grading

        Raises:
            GradingError: If grading fails
        """
        try:
            attempted_answer = AttemptedAnswer(
                question_type=self._context.validated_data["question_type"],
                question_metadata=self._context.validated_data["question_metadata"],
            )

            grading_result = self._deps.grading_service.grade_attempt(
                assessment_data["grader"],
                assessment_data["user_id"],
                attempted_answer,
                assessment_data["question"],
                assessment_data["question_attempt"],
            )

            return grading_result

        except GradingError:
            raise
        except Exception as e:
            logger.error(f"Failed to grade attempt: {e}")
            raise GradingError(
                f"Failed to grade question {assessment_data['question_id']}"
            ) from e

    async def _handle_successful_attempt(
        self, assessment_data: dict, grading_result
    ) -> None:
        """
        Handle a successful attempt by saving it to the database.

        Args:
            assessment_data: Prepared assessment data
            grading_result: Result of grading

        Raises:
            QuestionAttemptError: If saving fails
        """
        try:
            grading_response_service = (
                self._deps.grader_factory.get_grading_response_service(
                    assessment_data["collection_name"]
                )
            )

            attempt_context = AttemptContext(
                user_id=assessment_data["user_id"],
                question=assessment_data["question"],
                question_id=assessment_data["question_id"],
                assessment_id=assessment_data["assessment_id"],
                question_attempt=assessment_data["question_attempt"],
                grading_result=grading_result,
                config=self._config,
            )

            await self._deps.attempt_saving_service.save_successful_attempt(
                attempt_context,
                self._deps.question_attempt_service,
                grading_response_service,
            )

        except Exception as e:
            logger.error(f"Failed to save successful attempt: {e}")
            raise QuestionAttemptError(
                f"Failed to save attempt for question {assessment_data['question_id']}"
            ) from e

    @staticmethod
    def _log_success(question_id: str, user_id: str) -> None:
        """Log successful attempt processing."""
        logger.info(
            "Successfully processed and saved attempt for question %s by user %s",
            question_id,
            user_id,
        )

    @staticmethod
    def _log_failure(question_id: str, feedback: str) -> None:
        """Log failed attempt processing."""
        logger.warning(
            "Question attempt for %s was not successful: %s", question_id, feedback
        )

    @classmethod
    def create_recorder(
        cls,
        resource_context: QuestionSetResources,
        config: Optional[GradingConfig] = None,
    ) -> "QuestionAttemptRecorder":
        """
        Factory method to create and configure a QuestionAttemptRecorder.

        Args:
            resource_context: Context containing validation data and resources
            config: Optional grading configuration

        Returns:
            A fully configured QuestionAttemptRecorder instance
        """
        collection_name = resource_context.resources.collection_name
        question_repo = MongoQuestionRepository.get_repo()

        dependencies = ServiceDependencies(
            assessment_service=AssessmentService(),
            question_service=QuestionService(
                question_repo=question_repo,
                collection_name=collection_name,
            ),
            grader_factory=GraderFactory(),
            grading_service=GradingService(config),
            attempt_saving_service=AttemptSavingService(config),
            question_attempt_service=QuestionAttemptService.get_service(
                collection_name, config
            ),
        )

        return cls(dependencies, resource_context)
