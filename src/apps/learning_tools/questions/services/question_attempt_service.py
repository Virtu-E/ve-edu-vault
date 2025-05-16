import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from src.apps.learning_tools.assessments.util import get_assessment_id
from src.lib.grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from src.lib.grade_book_v2.question_grading.qn_grading_service import (
    SingleQuestionGrader,
)
from src.lib.grade_book_v2.question_grading.qn_grading_types import (
    AttemptedAnswer,
    GradingResponse,
)
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt
from src.repository.question_repository.qn_repository_data_types import Question
from src.utils.mixins.context import ServiceResources

log = logging.getLogger(__name__)


@dataclass
class RecordQuestionAttemptResponse:
    question_id: str
    grading_result: GradingResponse


class AssessmentService:
    """Service for handling assessment-related operations."""

    @staticmethod
    async def get_assessment_id(education_context: ServiceResources) -> UUID:
        """Get the assessment ID for the current context."""
        assessment_id = await get_assessment_id(
            user=education_context.resources.user,
            learning_objective=education_context.resources.learning_objective,
        )
        log.debug("Using assessment ID %s", assessment_id)
        return assessment_id


class QuestionService:
    """Service for fetching and managing questions."""

    @staticmethod
    async def fetch_question_and_attempt(
        education_context: ServiceResources,
        grader: SingleQuestionGrader,
        question_id: str,
        user_id: str,
        assessment_id: UUID,
    ) -> Tuple[Question, Optional[StudentQuestionAttempt]]:
        """Fetch the question and any existing attempt."""
        question, question_attempt = await asyncio.gather(
            education_context.service.get_question_by_id(question_id),
            grader.get_question_attempt(
                user_id=user_id,
                question_id=question_id,
                assessment_id=assessment_id,
            ),
        )
        log.debug("Successfully fetched question and existing attempt")
        return question, question_attempt

    @staticmethod
    def create_attempted_answer(
        education_context: ServiceResources,
    ) -> AttemptedAnswer:
        """Create an AttemptedAnswer object from the context data."""
        return AttemptedAnswer(
            question_type=education_context.validated_data["question_type"],
            question_metadata=education_context.validated_data["question_metadata"],
        )


class GraderFactory:
    """Factory for creating graders and related services."""

    @staticmethod
    def get_grader(collection_name: str) -> SingleQuestionGrader:
        """Get the appropriate grader for the collection."""
        return SingleQuestionGrader.get_grader(collection_name)

    @staticmethod
    def get_grading_response_service(collection_name: str) -> GradingResponseService:
        """Get the appropriate grading response service for the collection."""
        return GradingResponseService.get_service(collection_name=collection_name)


class GradingService:
    """Service for grading question attempts."""

    @staticmethod
    def grade_attempt(
        grader: SingleQuestionGrader,
        user_id: str,
        attempted_answer: AttemptedAnswer,
        question: Question,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> GradingResponse:
        """Grade the question attempt."""
        log.debug("Grading question attempt for question %s", question.id)
        return grader.grade(
            user_id=user_id,
            attempted_answer=attempted_answer,
            question=question,
            question_attempt=question_attempt,
        )


class AttemptSavingService:
    """Service for saving graded attempts."""

    @staticmethod
    async def save_successful_attempt(
        grader: SingleQuestionGrader,
        grading_response_service: GradingResponseService,
        user_id: str,
        question: Question,
        question_id: str,
        grading_result: GradingResponse,
        assessment_id: UUID,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> None:
        """Save a successful attempt to the database."""
        log.debug(
            "Saving successful attempt for question %s, correct: %s, score: %s",
            question_id,
            grading_result.is_correct,
            grading_result.score,
        )

        await asyncio.gather(
            grader.save_attempt(
                user_id=user_id,
                question=question,
                is_correct=grading_result.is_correct,
                score=grading_result.score,
                assessment_id=assessment_id,
                question_attempt=question_attempt,
            ),
            grading_response_service.save_grading_response(
                user_id=user_id,
                question_id=question_id,
                assessment_id=assessment_id,
                grading_response=grading_result,
                question_type=question.question_type,
            ),
        )


class QuestionAttemptRecorder:
    """
    Coordinates the process of recording a question attempt by orchestrating
    the various services needed in the workflow.
    """

    def __init__(
        self,
        assessment_service: AssessmentService,
        question_service: QuestionService,
        grader_factory: GraderFactory,
        grading_service: GradingService,
        attempt_saving_service: AttemptSavingService,
        education_context: ServiceResources,
    ) -> None:
        """
        Initialize the recorder with its dependencies.

        Args:
            assessment_service: Service for assessment-related operations
            question_service: Service for question-related operations
            grader_factory: Factory for creating graders
            grading_service: Service for grading attempts
            attempt_saving_service: Service for saving attempts
        """
        self._assessment_service = assessment_service
        self._question_service = question_service
        self._grader_factory = grader_factory
        self._grading_service = grading_service
        self._attempt_saving_service = attempt_saving_service
        self._education_context = education_context

    async def record_assessment(self) -> RecordQuestionAttemptResponse:
        """
        Main entry point for recording a question attempt.
        Returns:
            RecordQuestionAttemptResponse: The result of the attempt.
        """
        question_id: str = self._education_context.validated_data["question_id"]
        user_id: str = self._education_context.resources.user.id
        collection_name: str = self._education_context.resources.collection_name

        log.debug("Processing attempt for question %s by user %s", question_id, user_id)

        grader: SingleQuestionGrader = self._grader_factory.get_grader(collection_name)
        assessment_id: UUID = await self._assessment_service.get_assessment_id(
            self._education_context
        )

        question, question_attempt = (
            await self._question_service.fetch_question_and_attempt(
                self._education_context, grader, question_id, user_id, assessment_id
            )
        )

        attempted_answer: AttemptedAnswer = (
            self._question_service.create_attempted_answer(self._education_context)
        )
        grading_result: GradingResponse = self._grading_service.grade_attempt(
            grader, user_id, attempted_answer, question, question_attempt
        )

        if grading_result.success:
            grading_response_service: GradingResponseService = (
                self._grader_factory.get_grading_response_service(collection_name)
            )
            await self._attempt_saving_service.save_successful_attempt(
                grader,
                grading_response_service,
                user_id,
                question,
                question_id,
                grading_result,
                assessment_id,
                question_attempt,
            )
            log.info(
                "Successfully processed and saved attempt for question %s by user %s",
                question_id,
                user_id,
            )
        else:
            log.warning(
                "Question attempt for %s was not successful: %s",
                question_id,
                grading_result.feedback,
            )

        return RecordQuestionAttemptResponse(
            question_id=question_id,
            grading_result=grading_result,
        )

    @classmethod
    def get_question_recorder(cls, education_context) -> "QuestionAttemptRecorder":
        """
        Create and configure a QuestionAttemptRecorder with all its dependencies.

        Returns:
            A fully configured QuestionAttemptRecorder instance.
        """
        return cls(
            assessment_service=AssessmentService(),
            question_service=QuestionService(),
            grader_factory=GraderFactory(),
            grading_service=GradingService(),
            attempt_saving_service=AttemptSavingService(),
            education_context=education_context,
        )
