import logging
from uuid import UUID

from src.apps.learning_tools.assessments.services.assessment_grading.utils import (
    AssessmentCompleteService,
    AssessmentDataFetcher,
    AssessmentGradingProcessor,
    AssessmentPreparingService,
    UnattemptedQuestionProcessor,
)
from src.library.grade_book_v2.assessment_grading.assessment_grader import (
    AssessmentGrader,
)
from src.library.grade_book_v2.assessment_grading.data_types import AssessmentResult
from src.library.grade_book_v2.assessment_grading.utils import UnattemptedQuestionFinder
from src.repository.question_repository.providers.question_provider import (
    QuestionProvider,
)
from src.repository.student_attempts.providers.factories import (
    StudentAttemptProviderFactory,
)
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


class AssessmentServiceFactory:
    """Factory for creating configured assessment services with all internal dependencies."""

    @staticmethod
    def create_assessment_services(
        assessment_id: UUID,
        resources_context: QuestionSetResources,
    ) -> AssessmentCompleteService:
        """
        Create fully configured assessment services with all dependencies.

        Args:
            assessment_id: UUID of the assessment
            resources_context: Question set resources context

        Returns:
            AssessmentCompleteService: Configured service ready for grading
        """
        logger.info(f"Creating assessment services for assessment_id: {assessment_id}")

        try:
            qn_provider = QuestionProvider.get_mongo_provider(resources_context)

            bulk_attempt_provider = (
                StudentAttemptProviderFactory.create_mongo_bulk_provider(
                    collection_name=resources_context.resources.collection_name,
                )
            )

            unattempted_qn_finder = UnattemptedQuestionFinder()

            assessment_grader = AssessmentGrader(
                user=resources_context.resources.user,
                learning_objective=resources_context.resources.learning_objective,
                assessment_id=assessment_id,
            )

            data_fetcher = AssessmentDataFetcher(
                assessment_id=assessment_id,
                qn_provider=qn_provider,
                bulk_attempt_provider=bulk_attempt_provider,
                resources_context=resources_context,
            )

            unattempted_processor = UnattemptedQuestionProcessor(
                assessment_id=assessment_id,
                bulk_attempt_provider=bulk_attempt_provider,
                unattempted_qn_finder=unattempted_qn_finder,
                resources_context=resources_context,
            )

            grading_processor = AssessmentGradingProcessor(
                assessment_grader=assessment_grader
            )

            preparing_service = AssessmentPreparingService(
                data_fetcher=data_fetcher,
                unattempted_processor=unattempted_processor,
            )

            complete_service = AssessmentCompleteService(
                preparing_service=preparing_service,
                grading_processor=grading_processor,
            )

            logger.info(
                f"Successfully created assessment services for assessment_id: {assessment_id}"
            )
            return complete_service

        except Exception as e:
            logger.error(
                f"Failed to create assessment services for assessment_id {assessment_id}: {e}"
            )
            raise


async def grade_assessment(
    *,
    assessment_id: UUID,
    resources_context: QuestionSetResources,
) -> AssessmentResult:
    """
    Convenience function to grade a complete assessment.

    Args:
        assessment_id: UUID of the assessment to grade
        resources_context: Question set resources context

    Returns:
        AssessmentResult: The complete grading result

    Raises:
        Exception: Any grading errors are logged and re-raised
    """
    logger.info(
        f"Starting complete assessment grading for assessment_id: {assessment_id}"
    )

    try:
        complete_service = AssessmentServiceFactory.create_assessment_services(
            assessment_id=assessment_id,
            resources_context=resources_context,
        )

        result = await complete_service.grade_assessment()

        logger.info(
            f"Complete assessment grading finished for assessment_id: {assessment_id}, "
            f"score: {result.overall_score:.2%}"
        )
        return result

    except Exception as e:
        logger.error(
            f"Complete assessment grading failed for assessment_id {assessment_id}: {e}"
        )
        raise
