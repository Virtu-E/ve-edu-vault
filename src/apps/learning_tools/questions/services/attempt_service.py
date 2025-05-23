import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from bson import ObjectId

from src.library.grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from src.repository.grading_repository.base_grading_repository import (
    AbstractGradingRepository,
)
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt
from src.repository.grading_repository.mongo_grading_repository import (
    MongoGradingRepository,
)
from src.repository.question_repository.qn_repository_data_types import Question

from ..exceptions import QuestionAttemptError
from .data_types import AttemptBuildContext, AttemptContext, GradingConfig

logger = logging.getLogger(__name__)


class AttemptDataBuilder(ABC):
    """Abstract interface for building attempt data"""

    @abstractmethod
    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        pass


class FirstAttemptBuilder(AttemptDataBuilder):
    """Strategy for building first attempt data"""

    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc)

        attempt = {
            "is_correct": context.is_correct,
            "score": context.score,
            "timestamp": current_time,
        }

        logger.debug(
            f"Creating first attempt record for user: {context.user_id}, question: {context.question.id}"
        )

        return {
            "$push": {"attempts": attempt},
            "$setOnInsert": {
                "user_id": context.user_id,
                "question_id": ObjectId(context.question.id),
                "created_at": current_time,
                "question_type": context.question.question_type,
                "topic": context.question.topic,
                "sub_topic": context.question.sub_topic,
                "learning_objective": context.question.learning_objective,
                "first_attempt_at": current_time,
                "question_metadata": context.question.model_dump(),
            },
            "$set": {
                "total_attempts": 1,
                "best_score": context.score,
                "latest_score": context.score,
                "mastered": context.is_correct
                and context.score >= context.config.mastery_threshold,
                "last_attempt_at": current_time,
            },
        }


class SubsequentAttemptBuilder(AttemptDataBuilder):
    """Strategy for building subsequent attempt data"""

    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc)

        attempt = {
            "is_correct": context.is_correct,
            "score": context.score,
            "timestamp": current_time,
        }

        total_attempts = (
            context.existing_attempt.total_attempts + 1
            if context.existing_attempt
            else 1
        )

        logger.debug(
            f"Updating existing attempt record for user: {context.user_id}, "
            f"question: {context.question.id}, attempt #: {total_attempts}"
        )

        update_operation = {
            "$push": {"attempts": attempt},
            "$inc": {"total_attempts": 1},
            "$set": {"latest_score": context.score, "last_attempt_at": current_time},
        }

        return update_operation


class AttemptDataBuilderFactory:
    """Factory for creating appropriate attempt data builders"""

    @staticmethod
    def get_builder(has_existing_attempt: bool) -> AttemptDataBuilder:
        if has_existing_attempt:
            return SubsequentAttemptBuilder()
        return FirstAttemptBuilder()


class QuestionAttemptService:
    """
    Service for managing student question attempts with improved error handling and configuration.

    This service handles the persistence and retrieval of student question
    attempt data, including tracking attempts, scores, and mastery status.
    """

    def __init__(
        self,
        grading_repository: AbstractGradingRepository,
        collection_name: str,
        config: Optional[GradingConfig] = None,
    ) -> None:
        """
        Initialize the QuestionAttemptService with repository and configuration.

        Args:
            grading_repository: The grading repository for data access
            collection_name: Name of the collection to use
            config: Grading configuration (defaults to collection-based config)
        """
        self.grading_repository = grading_repository
        self.collection_name = collection_name
        self.config = config or GradingConfig()

        logger.info(
            f"QuestionAttemptService initialized with collection: {collection_name}, "
            f"mastery_threshold: {self.config.mastery_threshold}, "
            f"max_attempts: {self.config.max_attempts}"
        )

    async def get_question_attempt(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
    ) -> Optional[StudentQuestionAttempt]:
        """
        Retrieve the current question attempt for a user and question.

        Args:
            user_id: Unique identifier for the student
            question_id: Unique identifier for the question
            assessment_id: Unique identifier for the assessment

        Returns:
            StudentQuestionAttempt object if found, None otherwise

        Raises:
            QuestionAttemptError: If retrieval fails
        """
        try:
            # Validate inputs
            if not user_id or not question_id:
                raise QuestionAttemptError("User ID and Question ID are required")

            logger.debug(
                f"Retrieving attempt for user: {user_id}, question: {question_id}"
            )

            attempt = await self.grading_repository.get_question_attempt_single(
                user_id=user_id,
                assessment_id=assessment_id,
                question_id=question_id,
                collection_name=self.collection_name,
            )

            logger.debug(f"Found attempt: {attempt is not None}")
            return attempt

        except QuestionAttemptError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve question attempt: {e}")
            raise QuestionAttemptError(
                f"Database error retrieving attempt for question {question_id}"
            ) from e

    def _build_save_attempt_data(
        self,
        user_id: str,
        question: Question,
        is_correct: bool,
        score: float,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> Dict[str, Any]:
        """
        Build the data structure for saving an attempt using strategy pattern.

        Args:
            user_id: Unique identifier for the student
            question: Question object containing metadata about the question
            is_correct: Whether the current attempt was correct
            score: Numerical score for the current attempt
            question_attempt: Previous attempt data if exists

        Returns:
            Dictionary containing the update operation for the repository
        """
        # Validate score
        if score < 0 or score > 1:
            raise QuestionAttemptError(
                f"Invalid score: {score}. Score must be between 0 and 1"
            )

        context = AttemptBuildContext(
            user_id=user_id,
            question=question,
            is_correct=is_correct,
            score=score,
            existing_attempt=question_attempt,
            config=self.config,
        )

        builder = AttemptDataBuilderFactory.get_builder(question_attempt is not None)
        return builder.build(context)

    async def save_attempt(
        self,
        user_id: str,
        question: Question,
        assessment_id: UUID,
        is_correct: bool,
        score: float,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> None:
        """
        Save an attempt to the repository.

        Args:
            user_id: Unique identifier for the student
            question: Question object containing metadata about the question
            is_correct: Whether the current attempt was correct
            score: Numerical score for the current attempt
            assessment_id: Unique identifier for the assessment
            question_attempt: Previous attempt data if exists

        Raises:
            QuestionAttemptError: If saving fails
        """
        try:
            # Validate inputs
            if not user_id or not question or not question.id:
                raise QuestionAttemptError("User ID and valid Question are required")

            logger.info(
                f"Saving attempt for user: {user_id}, question: {question.id}, "
                f"correct: {is_correct}, score: {score}"
            )

            # Check attempt limits if configured
            if (
                self.config.max_attempts
                and question_attempt
                and question_attempt.total_attempts >= self.config.max_attempts
            ):
                raise QuestionAttemptError(
                    f"Maximum attempts ({self.config.max_attempts}) exceeded for question {question.id}"
                )

            document_to_update = self._build_save_attempt_data(
                user_id=user_id,
                question=question,
                is_correct=is_correct,
                score=score,
                question_attempt=question_attempt,
            )

            await self.grading_repository.save_attempt(
                user_id=user_id,
                question_id=question.id,
                assessment_id=assessment_id,
                update=document_to_update,
                collection_name=self.collection_name,
            )

            logger.debug(
                f"Attempt saved successfully for user: {user_id}, question: {question.id}"
            )

        except QuestionAttemptError:
            raise
        except Exception as e:
            logger.error(f"Failed to save attempt: {e}")
            raise QuestionAttemptError(
                f"Database error saving attempt for question {question.id}"
            ) from e

    @classmethod
    def get_service(
        cls, collection_name: str, config: Optional[GradingConfig] = None
    ) -> "QuestionAttemptService":
        """
        Factory method to create a QuestionAttemptService instance.

        Args:
            collection_name: Name of the collection to use
            config: Optional grading configuration

        Returns:
            QuestionAttemptService instance
        """
        logger.info(
            f"Creating new QuestionAttemptService with collection: {collection_name}"
        )
        return cls(
            grading_repository=MongoGradingRepository.get_repo(),
            collection_name=collection_name,
            config=config,
        )


class AttemptSavingService:
    """Service for saving graded attempts with improved error handling and validation"""

    def __init__(self, config: Optional[GradingConfig] = None):
        self.config = config or GradingConfig()

    async def save_successful_attempt(
        self,
        context: AttemptContext,
        question_attempt_service: QuestionAttemptService,
        grading_response_service: GradingResponseService,
    ) -> None:
        """
        Save a successful attempt to the database using context object.

        Args:
            context: Contains all the attempt information
            question_attempt_service: Service for saving question attempts
            grading_response_service: Service for saving grading responses

        Raises:
            QuestionAttemptError: If saving fails
        """
        try:
            # Validate context
            self._validate_attempt_context(context)

            logger.debug(
                "Saving successful attempt for question %s, correct: %s, score: %s",
                context.question_id,
                context.grading_result.is_correct,
                context.grading_result.score,
            )

            # Save both attempt and grading response concurrently
            await asyncio.gather(
                question_attempt_service.save_attempt(
                    user_id=context.user_id,
                    question=context.question,
                    is_correct=context.grading_result.is_correct,
                    score=context.grading_result.score,
                    assessment_id=context.assessment_id,
                    question_attempt=context.question_attempt,
                ),
                grading_response_service.save_grading_response(
                    user_id=context.user_id,
                    question_id=context.question_id,
                    assessment_id=context.assessment_id,
                    grading_response=context.grading_result,
                    question_type=context.question.question_type,
                ),
            )

            logger.info(
                f"Successfully saved attempt for question {context.question_id}"
            )

        except QuestionAttemptError:
            raise
        except Exception as e:
            logger.error(f"Failed to save successful attempt: {e}")
            raise QuestionAttemptError(
                f"Failed to save attempt for question {context.question_id}"
            ) from e

    @staticmethod
    def _validate_attempt_context(context: AttemptContext) -> None:
        """Validate attempt context before saving."""
        if not context.user_id:
            raise QuestionAttemptError("User ID is required")
        if not context.question_id:
            raise QuestionAttemptError("Question ID is required")
        if not context.question:
            raise QuestionAttemptError("Question object is required")
        if not context.grading_result:
            raise QuestionAttemptError("Grading result is required")
        if not context.assessment_id:
            raise QuestionAttemptError("Assessment ID is required")
