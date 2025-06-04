import asyncio
import logging
from uuid import UUID

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


async def grade_assessment(
    assessment_id: UUID,
    resources_context: QuestionSetResources,
) -> AssessmentResult:
    """
    Grade a complete assessment with all necessary steps.

    Args:
        assessment_id: UUID of the assessment to grade
        resources_context: Question set resources context

    Returns:
        AssessmentResult: Complete grading results
    """
    logger.info(f"Starting assessment grading for {assessment_id}")
    qn_provider = QuestionProvider.get_mongo_provider(resources_context)
    bulk_attempt_provider = StudentAttemptProviderFactory.create_mongo_bulk_provider(
        collection_name=resources_context.resources.collection_name
    )
    unattempted_finder = UnattemptedQuestionFinder()
    grader = AssessmentGrader(
        user=resources_context.resources.user,
        learning_objective=resources_context.resources.learning_objective,
        assessment_id=assessment_id,
    )

    questions, attempts = await asyncio.gather(
        qn_provider.get_questions_from_ids(
            resources_context.resources.question_set_ids
        ),
        bulk_attempt_provider.get_bulk_qn_attempts(
            user_id=resources_context.resources.user.id, assessment_id=assessment_id
        ),
    )

    logger.info(f"Fetched {len(questions)} questions and {len(attempts)} attempts")

    unattempted_questions = unattempted_finder.find_unattempted(questions, attempts)
    if unattempted_questions:
        records_created = await bulk_attempt_provider.bulk_create_unanswered_attempts(
            student_user_id=resources_context.resources.user.id,
            assessment_id=assessment_id,
            unanswered_questions=unattempted_questions,
        )
        logger.info(f"Created {records_created} unanswered attempt records")

        # Refetch attempts to include newly created ones
        attempts = await bulk_attempt_provider.get_bulk_qn_attempts(
            user_id=resources_context.resources.user.id, assessment_id=assessment_id
        )

    # Grade the assessment
    result = await grader.grade_assessment(attempts)

    logger.info(f"Assessment grading completed: {result.overall_score:.2%}")
    return result
