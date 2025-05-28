import logging
from typing import Optional
from uuid import UUID

from src.apps.learning_tools.assessments.selectors.assessment import AssessmentSelector
from src.apps.learning_tools.questions.exceptions import MaximumAttemptsError
from src.apps.learning_tools.questions.services.data_types import AssessmentContext
from src.apps.learning_tools.questions.services.graded_responses import (
    GradedResponseService,
)
from src.apps.learning_tools.questions.services.question_grader.grading_services import (
    GradingDataService,
    GradingExecutionService,
    GradingResultService,
)
from src.library.grade_book_v2.question_grading.question_grader import (
    SingleQuestionGrader,
)
from src.repository.graded_responses.data_types import GradedResponse, StudentAnswer
from src.repository.question_repository.providers.question_provider import (
    QuestionProvider,
)
from src.repository.student_attempts.providers.data_types import GradingConfig
from src.repository.student_attempts.providers.factories import (
    StudentAttemptProviderFactory,
)
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


class StudentGradingMediator:
    """Coordinates the complete grading workflow through service orchestration."""

    def __init__(
        self,
        data_service: GradingDataService,
        grading_service: GradingExecutionService,
        result_service: GradingResultService,
        context: AssessmentContext,
    ):
        """
        Initialize mediator with required services and context.

        Args:
            data_service: Handles grading data preparation
            grading_service: Executes grading logic
            result_service: Processes and saves results
            context: Assessment context with user and question info
        """
        self.data_service = data_service
        self.grading_service = grading_service
        self.result_service = result_service
        self.context = context

        logger.info(
            "StudentGradingMediator initialized for user_id=%s, question_id=%s",
            context.user_id,
            context.question_id,
        )

    async def grade_submission(self, assessment_id: UUID) -> GradedResponse:
        """
        Execute complete grading workflow.

        Args:
            assessment_id: UUID of the assessment to grade

        Returns:
            GradedResponse: Final graded result

        Raises:
            Exception: Re-raises any grading errors after logging
        """
        logger.info(
            "Starting grading workflow for assessment_id=%s, user_id=%s, question_id=%s",
            assessment_id,
            self.context.user_id,
            self.context.question_id,
        )

        try:
            logger.debug("Preparing grading data for assessment_id=%s", assessment_id)
            grading_data = await self.data_service.prepare_grading_data(
                self.context, assessment_id
            )

            history = grading_data.previous_attempt_history

            if (
                # TODO: remove hard coded number value
                history
                and history.total_attempts == 3
            ):
                raise MaximumAttemptsError(
                    "User has exceeded the maximum number of attempts"
                )

            logger.debug("Executing grading for assessment_id=%s", assessment_id)
            result = await self.grading_service.execute_grading(grading_data)

            logger.debug("Processing results for assessment_id=%s", assessment_id)

            if not history or not history.mastered:
                await self.result_service.process_result(
                    result=result,
                    context=self.context,
                    target_question=grading_data.target_question,
                    previous_attempt=grading_data.previous_attempt_history,
                )

            logger.info(
                "Successfully completed grading workflow for assessment_id=%s, score=%s",
                assessment_id,
                getattr(result, "score", "unknown"),
            )
            return result

        except Exception as e:
            logger.error(
                "Grading workflow failed for assessment_id=%s, user_id=%s: %s",
                assessment_id,
                self.context.user_id,
                str(e),
            )
            raise


class GradingMediatorFactory:
    """Factory for creating configured grading mediators."""

    @staticmethod
    def create_grading_mediator(
        question_resources: QuestionSetResources,
        assessment_id: UUID,
        grading_config: Optional[GradingConfig] = None,
    ) -> StudentGradingMediator:
        """
        Create a fully configured grading mediator.

        Args:
            question_resources: Resources containing question and user context
            assessment_id: UUID of the assessment
            grading_config: Optional grading configuration

        Returns:
            StudentGradingMediator: Configured mediator ready for grading
        """
        logger.info(
            "Creating grading mediator for assessment_id=%s, user_id=%s",
            assessment_id,
            question_resources.resources.user.id,
        )

        try:

            attempt_provider = (
                StudentAttemptProviderFactory.create_mongo_attempt_provider(
                    question_resources.resources.collection_name
                )
            )

            data_service = GradingDataService(
                question_provider=QuestionProvider.get_mongo_provider(
                    question_resources
                ),
                attempt_provider=attempt_provider,
            )

            grading_service = GradingExecutionService(grader=SingleQuestionGrader())

            result_service = GradingResultService(
                response_service=GradedResponseService.get_service(question_resources),
                attempt_provider=attempt_provider,
            )

            current_submission = StudentAnswer(
                question_type=question_resources.validated_data["question_type"],
                question_metadata=question_resources.validated_data[
                    "question_metadata"
                ],
            )

            context = AssessmentContext(
                user_id=question_resources.resources.user.id,
                question_id=question_resources.validated_data["question_id"],
                collection_name=question_resources.resources.collection_name,
                submitted_answer=current_submission,
                assessment_id=assessment_id,
            )

            mediator = StudentGradingMediator(
                data_service=data_service,
                grading_service=grading_service,
                result_service=result_service,
                context=context,
            )

            logger.info(
                "Successfully created grading mediator for assessment_id=%s",
                assessment_id,
            )
            return mediator

        except Exception as e:
            logger.error(
                "Failed to create grading mediator for assessment_id=%s: %s",
                assessment_id,
                str(e),
            )
            raise


async def grade_student_submission(
    *, resource_context: QuestionSetResources
) -> GradedResponse:
    """
    Convenience function to grade a student submission.

    Args:
        resource_context: Resources containing question and user context

    Returns:
        GradedResponse: The graded result

    Raises:
        Exception: Any grading errors are logged and re-raised
    """
    selector = AssessmentSelector(resource_context=resource_context)
    assessment_id = await selector.get_assessment_id()
    logger.info(
        "Starting student submission grading for assessment_id=%s", assessment_id
    )

    try:
        mediator = GradingMediatorFactory.create_grading_mediator(
            resource_context, assessment_id
        )
        result = await mediator.grade_submission(assessment_id)

        logger.info(
            "Student submission grading completed for assessment_id=%s, score=%s",
            assessment_id,
            getattr(result, "score", "unknown"),
        )
        return result

    except Exception as e:
        logger.error(
            "Student submission grading failed for assessment_id=%s: %s",
            assessment_id,
            str(e),
        )
        raise
