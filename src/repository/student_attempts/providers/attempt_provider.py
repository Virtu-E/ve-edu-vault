import logging
from typing import Any, Dict, Optional
from uuid import UUID

from src.repository.question_repository.data_types import Question
from src.repository.question_repository.exceptions import QuestionAttemptError

from ..data_types import StudentQuestionAttempt
from ..mongo.attempts_repo import MongoAttemptRepository
from .data_types import AttemptBuildContext, GradingConfig
from .validators import AttemptValidationService

logger = logging.getLogger(__name__)


class StudentAttemptProvider:
    """
    Provider for managing individual student question attempts.

    Provides access to attempt data retrieval, persistence, and validation
    for single question attempts across different assessments.
    """

    def __init__(
        self,
        attempt_repository: MongoAttemptRepository,
        collection_name: str,
        grading_config: Optional[GradingConfig] = None,
    ) -> None:
        """
        Initialize attempt provider with repository and configuration.

        Args:
            attempt_repository: Repository for data access
            collection_name: Database collection name
            grading_config: Configuration for grading behavior
        """
        self.attempt_repository = attempt_repository
        self.collection_name = collection_name
        self.grading_config = grading_config or GradingConfig()
        self.attempt_validator = AttemptValidationService(self.grading_config)

        logger.info(
            f"StudentAttemptProvider initialized with collection: {collection_name}, "
            f"mastery_threshold: {self.grading_config.mastery_threshold}, "
            f"max_attempts: {self.grading_config.max_attempts}"
        )

    async def get_question_attempt(
        self,
        student_user_id: str,
        question_id: str,
        assessment_id: UUID,
    ) -> Optional[StudentQuestionAttempt]:
        """
        Retrieve existing attempt data for a specific question.

        Args:
            student_user_id: Student's unique identifier
            question_id: Question's unique identifier
            assessment_id: Assessment's unique identifier

        Returns:
            Existing attempt data if found, None otherwise
        """
        try:
            self.attempt_validator.validate_retrieval_inputs(
                student_user_id, question_id
            )

            logger.debug(
                f"Retrieving attempt for user: {student_user_id}, question: {question_id}"
            )

            existing_attempt = (
                await self.attempt_repository.get_question_attempt_single(
                    user_id=student_user_id,
                    assessment_id=assessment_id,
                    question_id=question_id,
                    collection_name=self.collection_name,
                )
            )

            logger.debug(f"Found attempt: {existing_attempt is not None}")
            return existing_attempt

        except QuestionAttemptError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve question attempt: {e}")
            raise QuestionAttemptError(
                f"Database error retrieving attempt for question {question_id}"
            ) from e

    def _build_attempt_update_data(
        self,
        student_user_id: str,
        question: Question,
        is_answer_correct: bool,
        attempt_score: float,
        existing_attempt: Optional[StudentQuestionAttempt],
    ) -> Dict[str, Any]:
        """
        Build database update operation for attempt persistence.

        Args:
            student_user_id: Student's unique identifier
            question: Question being attempted
            is_answer_correct: Whether the answer was correct
            attempt_score: Numerical score achieved
            existing_attempt: Previous attempt data if exists

        Returns:
            Database update operation dictionary
        """
        build_context = AttemptBuildContext(
            user_id=student_user_id,
            question=question,
            is_correct=is_answer_correct,
            score=attempt_score,
            existing_attempt=existing_attempt,
            config=self.grading_config,
        )
        from .factories import AttemptDataBuilderFactory

        attempt_builder = AttemptDataBuilderFactory.get_builder(
            existing_attempt is not None
        )
        return attempt_builder.build(build_context)

    async def save_attempt(
        self,
        student_user_id: str,
        question: Question,
        assessment_id: UUID,
        is_answer_correct: bool,
        attempt_score: float,
        existing_attempt: Optional[StudentQuestionAttempt],
    ) -> None:
        """
        Persist a single question attempt to the database.

        Args:
            student_user_id: Student's unique identifier
            question: Question being attempted
            assessment_id: Assessment's unique identifier
            is_answer_correct: Whether the answer was correct
            attempt_score: Numerical score achieved
            existing_attempt: Previous attempt data if exists
        """
        try:
            self.attempt_validator.validate_attempt_inputs(
                student_user_id, question, attempt_score
            )
            self.attempt_validator.validate_attempt_limits(
                existing_attempt, question.id
            )

            logger.info(
                f"Saving attempt for user: {student_user_id}, question: {question.id}, "
                f"correct: {is_answer_correct}, score: {attempt_score}"
            )

            update_operation = self._build_attempt_update_data(
                student_user_id=student_user_id,
                question=question,
                is_answer_correct=is_answer_correct,
                attempt_score=attempt_score,
                existing_attempt=existing_attempt,
            )

            await self.attempt_repository.save_attempt(
                user_id=student_user_id,
                question_id=question.id,
                assessment_id=assessment_id,
                update=update_operation,
                collection_name=self.collection_name,
            )

            logger.debug(
                f"Attempt saved successfully for user: {student_user_id}, question: {question.id}"
            )

        except QuestionAttemptError:
            raise
        except Exception as e:
            logger.error(f"Failed to save attempt: {e}")
            raise QuestionAttemptError(
                f"Database error saving attempt for question {question.id}"
            ) from e
