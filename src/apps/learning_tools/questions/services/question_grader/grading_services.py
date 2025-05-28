import asyncio
import logging
from uuid import UUID

from src.apps.learning_tools.questions.services.data_types import (
    AssessmentContext,
    GradingContext,
)
from src.apps.learning_tools.questions.services.graded_responses import (
    GradedResponseService,
)
from src.exceptions import QuestionNotFoundError
from src.library.grade_book_v2.question_grading.question_grader import (
    SingleQuestionGrader,
)
from src.repository.graded_responses.data_types import GradedResponse
from src.repository.question_repository.providers.question_provider import (
    QuestionProvider,
)
from src.repository.student_attempts.providers.attempt_provider import (
    StudentAttemptProvider,
)

logger = logging.getLogger(__name__)


class GradingDataService:
    """
    Handles data preparation for grading operations.

    Attributes:
        question_provider (QuestionProvider): Provider for accessing question data
        attempt_provider (StudentAttemptProvider): Provider for accessing student attempt data
    """

    def __init__(
        self,
        question_provider: QuestionProvider,
        attempt_provider: StudentAttemptProvider,
    ):
        """
        Initialize the GradingDataService with required providers.

        Args:
            question_provider (QuestionProvider): Service for retrieving question data
            attempt_provider (StudentAttemptProvider): Service for retrieving student attempt data
        """
        self.question_provider = question_provider
        self.attempt_provider = attempt_provider
        logger.info("GradingDataService initialized")

    async def prepare_grading_data(
        self, context: AssessmentContext, assessment_id: UUID
    ) -> GradingContext:
        """
        Prepare all necessary data for grading a student's answer.

        Concurrently fetches the target question and any previous attempt history
        for the student. This data is then packaged into a GradingContext object
        that contains everything needed for the grading process.

        Args:
            context (AssessmentContext): Contains question ID, user ID, and submitted answer
            assessment_id (UUID): Unique identifier for the assessment being graded

        Returns:
            GradingContext: Complete context object containing all grading data

        Raises:
            QuestionNotFoundError: If the target question cannot be found

        """
        logger.info(
            "Preparing grading data for question_id=%s, user_id=%s, assessment_id=%s",
            context.question_id,
            context.user_id,
            assessment_id,
        )

        try:
            target_question, previous_attempt = await asyncio.gather(
                self.question_provider.get_question_by_id(context.question_id),
                self.attempt_provider.get_question_attempt(
                    student_user_id=context.user_id,
                    question_id=context.question_id,
                    assessment_id=assessment_id,
                ),
            )

            logger.debug(
                "Successfully retrieved question (found=%s) and previous attempt (found=%s)",
                target_question is not None,
                previous_attempt is not None,
            )

        except Exception as e:
            logger.error(
                "Failed to fetch grading data for question_id=%s, user_id=%s: %s",
                context.question_id,
                context.user_id,
                str(e),
            )
            raise

        if not target_question:
            logger.warning(
                "Question not found: question_id=%s, user_id=%s",
                context.question_id,
                context.user_id,
            )
            raise QuestionNotFoundError(
                question_id=context.question_id, username=context.user_id
            )

        grading_context = GradingContext(
            target_question=target_question,
            previous_attempt_history=previous_attempt,
            student_user_id=context.user_id,
            submitted_answer=context.submitted_answer,
        )

        logger.info(
            "Successfully prepared grading data for question_id=%s, user_id=%s",
            context.question_id,
            context.user_id,
        )

        return grading_context


class GradingExecutionService:
    """
    Handles the actual grading logic execution.

    This service is responsible for executing the grading algorithm using the
    provided grading context. It acts as a wrapper around the SingleQuestionGrader
    to provide consistent logging and error handling.

    Attributes:
        grader (SingleQuestionGrader): The grading engine that performs actual grading
    """

    def __init__(self, grader: SingleQuestionGrader):
        """
        Initialize the GradingExecutionService with a grader instance.

        Args:
            grader (SingleQuestionGrader): The grading engine to use for scoring answers
        """
        self.grader = grader
        logger.info(
            "GradingExecutionService initialized with grader: %s", type(grader).__name__
        )

    async def execute_grading(self, grading_data: GradingContext) -> GradedResponse:
        """
        Execute the grading process for a student's answer.

        Args:
            grading_data (GradingContext): Complete context containing question, answer,
                                         and attempt history

        Returns:
            GradedResponse: The graded response containing score, feedback, and metadata

        Raises:
            Exception: Any grading errors are logged and re-raised

        """
        logger.info(
            "Executing grading for user_id=%s, question_id=%s",
            grading_data.student_user_id,
            grading_data.target_question.id,
        )

        try:
            result = self.grader.grade(**grading_data.to_dict)

            logger.info(
                "Grading completed successfully for user_id=%s, question_id=%s, score=%s",
                grading_data.student_user_id,
                grading_data.target_question.id,
                getattr(result, "score", "unknown"),
            )

            return result

        except Exception as e:
            logger.error(
                "Grading execution failed for user_id=%s, question_id=%s: %s",
                grading_data.student_user_id,
                grading_data.target_question.id,
                str(e),
            )
            raise


class GradingResultService:
    """
    Handles post-grading result processing and persistence.

    Attributes:
        response_service (GradedResponseService): Service for persisting graded responses
    """

    def __init__(self, response_service: GradedResponseService):
        """
        Initialize the GradingResultService with a response service.

        Args:
            response_service (GradedResponseService): Service for saving graded responses
        """
        self.response_service = response_service
        logger.info("GradingResultService initialized")

    async def process_result(
        self, result: GradedResponse, context: AssessmentContext
    ) -> GradedResponse:
        """
        Process and persist a graded response.

        Takes a graded response and handles all post-grading operations including
        validation, formatting, and saving to persistent storage. Future enhancements
        could include additional processing steps like notifications or analytics.

        Args:
            result (GradedResponse): The graded response to process
            context (AssessmentContext): Original assessment context for additional metadata

        Returns:
            GradedResponse: The processed graded response (may include additional metadata)

        Raises:
            Exception: Any persistence errors are logged and re-raised

        """
        logger.info(
            "Processing grading result for user_id=%s, assessment_id=%s, score=%s",
            context.user_id,
            context.assessment_id,
            getattr(result, "score", "unknown"),
        )

        try:
            await self.response_service.save_graded_response(
                result, context.assessment_id
            )

            logger.info(
                "Successfully saved graded response for user_id=%s, assessment_id=%s",
                context.user_id,
                context.assessment_id,
            )

            # Future enhancements could include:
            # - Result validation
            # - Response formatting
            # - Notification sending
            # - Analytics tracking

            return result

        except Exception as e:
            logger.error(
                "Failed to process grading result for user_id=%s, assessment_id=%s: %s",
                context.user_id,
                context.assessment_id,
                str(e),
            )
            raise
