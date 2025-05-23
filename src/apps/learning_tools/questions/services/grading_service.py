import logging
from typing import List, Optional

from src.library.grade_book_v2.question_grading.data_types import (
    AttemptedAnswer,
    GradingResponse,
)
from src.library.grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from src.library.grade_book_v2.question_grading.question_grader import (
    SingleQuestionGrader,
)
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt
from src.repository.grading_response_repository.response_data_types import (
    GradedResponse,
)
from src.repository.question_repository.qn_repository_data_types import Question
from src.utils.mixins.question_mixin import QuestionSetResources

from ...assessments.util import get_assessment_id
from ..exceptions import GradingError, MaximumAttemptsError, QuestionAttemptError
from .data_types import GradingConfig

logger = logging.getLogger(__name__)


class GraderFactory:
    """Factory for creating graders and related services with error handling."""

    _grader_cache = {}
    _service_cache = {}

    @classmethod
    def get_grader(cls, collection_name: str) -> SingleQuestionGrader:
        """
        Get the appropriate grader for the collection with caching.

        Args:
            collection_name: Name of the collection

        Returns:
            SingleQuestionGrader: The grader instance

        Raises:
            QuestionAttemptError: If grader cannot be created
        """
        try:
            if collection_name not in cls._grader_cache:
                grader = SingleQuestionGrader.get_grader(collection_name)
                cls._grader_cache[collection_name] = grader
                logger.debug(
                    f"Created and cached grader for collection: {collection_name}"
                )
            else:
                logger.debug(f"Using cached grader for collection: {collection_name}")

            return cls._grader_cache[collection_name]

        except Exception as e:
            logger.error(
                f"Failed to create grader for collection {collection_name}: {e}"
            )
            raise QuestionAttemptError(
                f"Failed to create grader for collection {collection_name}"
            ) from e

    @classmethod
    def get_grading_response_service(
        cls, collection_name: str
    ) -> GradingResponseService:
        """
        Get the appropriate grading response service for the collection with caching.

        Args:
            collection_name: Name of the collection

        Returns:
            GradingResponseService: The service instance

        Raises:
            QuestionAttemptError: If service cannot be created
        """
        try:
            if collection_name not in cls._service_cache:
                service = GradingResponseService.get_service(
                    collection_name=collection_name
                )
                cls._service_cache[collection_name] = service
                logger.debug(
                    f"Created and cached grading response service for collection: {collection_name}"
                )
            else:
                logger.debug(
                    f"Using cached grading response service for collection: {collection_name}"
                )

            return cls._service_cache[collection_name]

        except Exception as e:
            logger.error(
                f"Failed to create grading response service for collection {collection_name}: {e}"
            )
            raise QuestionAttemptError(
                f"Failed to create grading response service for collection {collection_name}"
            ) from e

    @classmethod
    def clear_cache(cls, collection_name: Optional[str] = None):
        """
        Clear the cache for a specific collection or all collections.

        Args:
            collection_name: Collection to clear, or None for all
        """
        if collection_name:
            cls._grader_cache.pop(collection_name, None)
            cls._service_cache.pop(collection_name, None)
            logger.info(f"Cleared cache for collection: {collection_name}")
        else:
            cls._grader_cache.clear()
            cls._service_cache.clear()
            logger.info("Cleared all grader and service caches")


class GradingService:
    """Service for grading question attempts with improved error handling and validation."""

    def __init__(self, config: Optional[GradingConfig] = None):
        self.config = config or GradingConfig()

    def grade_attempt(
        self,
        grader: SingleQuestionGrader,
        user_id: str,
        attempted_answer: AttemptedAnswer,
        question: Question,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> GradingResponse:
        """
        Grade the question attempt with validation and error handling.

        Args:
            grader: The grader to use
            user_id: ID of the user attempting the question
            attempted_answer: The user's attempted answer
            question: The question being attempted
            question_attempt: Previous attempt data if exists

        Returns:
            GradingResponse: Result of the grading

        Raises:
            GradingError: If grading fails
        """
        try:
            # Validate inputs
            self._validate_grading_inputs(user_id, attempted_answer, question)

            # Check attempt limits
            self._check_attempt_limits(question_attempt)

            logger.debug(
                "Grading question attempt for question %s by user %s",
                question.id,
                user_id,
            )

            grading_result = grader.grade(
                user_id=user_id,
                attempted_answer=attempted_answer,
                question=question,
                question_attempt=question_attempt,
            )

            self._validate_grading_result(grading_result, question.id)

            logger.debug(
                "Grading completed for question %s: correct=%s, score=%s",
                question.id,
                grading_result.is_correct,
                grading_result.score,
            )

            return grading_result

        except GradingError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to grade question {question.id} for user {user_id}: {e}"
            )
            raise GradingError(f"Failed to grade question {question.id}") from e

    @staticmethod
    def _validate_grading_inputs(
        user_id: str, attempted_answer: AttemptedAnswer, question: Question
    ):
        """Validate inputs before grading."""
        if not user_id:
            raise GradingError("User ID is required for grading")
        if not attempted_answer:
            raise GradingError("Attempted answer is required for grading")
        if not question:
            raise GradingError("Question is required for grading")
        if not question.id:
            raise GradingError("Question must have a valid ID")

    def _check_attempt_limits(self, question_attempt: Optional[StudentQuestionAttempt]):
        """Check if the user has exceeded attempt limits."""
        if (
            self.config.max_attempts
            and question_attempt
            and question_attempt.total_attempts >= self.config.max_attempts
        ):
            raise MaximumAttemptsError(
                f"Maximum attempts ({self.config.max_attempts}) exceeded"
            )

    @staticmethod
    def _validate_grading_result(grading_result: GradingResponse, question_id: str):
        """Validate the grading result."""
        if not grading_result:
            raise GradingError(f"Grading result is None for question {question_id}")
        if grading_result.score < 0 or grading_result.score > 1:
            raise GradingError(
                f"Invalid score {grading_result.score} for question {question_id}"
            )


async def get_graded_responses(
    *, resource_context: QuestionSetResources
) -> List[GradedResponse]:
    """
    Retrieve all question attempts for a specific user and learning objective.

    Args:
        resource_context: Context containing user and learning objective info

    Returns:
        List[GradedResponse]: List of graded responses

    Raises:
        QuestionAttemptError: If retrieval fails
    """
    try:
        user_id = resource_context.resources.user.id
        collection_name = resource_context.resources.collection_name

        logger.debug(
            "Getting graded responses for user %s, collection %s",
            user_id,
            collection_name,
        )

        grading_response_service = GraderFactory.get_grading_response_service(
            collection_name
        )

        assessment_id = await get_assessment_id(
            user=resource_context.resources.user,
            learning_objective=resource_context.resources.learning_objective,
        )

        logger.debug("Got assessment ID %s for user %s", assessment_id, user_id)

        question_attempts = await grading_response_service.get_grading_responses(
            user_id=user_id,
            collection_name=collection_name,
            assessment_id=assessment_id,
        )

        logger.info(
            "Retrieved %d question attempts for user %s",
            len(question_attempts),
            user_id,
        )

        return question_attempts

    except Exception as e:
        logger.error(f"Failed to get graded responses: {e}")
        raise QuestionAttemptError("Failed to retrieve graded responses") from e
