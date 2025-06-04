import logging

from src.apps.learning_tools.assessments.selectors.assessment import AssessmentSelector
from src.apps.learning_tools.questions.services.question_grader.utils import (
    execute_grading,
    prepare_grading_data,
    save_grading_results,
)
from src.exceptions import MaximumAttemptsExceededError
from src.repository.graded_responses.data_types import GradedResponse, StudentAnswer
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


async def grade_student_submission(
    *,
    resource_context: QuestionSetResources,
) -> GradedResponse:
    """
    Grade a student submission with all necessary steps.

    This is the main entry point that orchestrates the complete grading workflow:
    1. Get assessment ID
    2. Prepare grading data (fetch question and attempt history)
    3. Check attempt limits
    4. Execute grading
    5. Save results (if not already mastered)

    Args:
        resource_context: Resources containing question and user context

    Returns:
        GradedResponse: The graded result

    Raises:
        MaximumAttemptsError: If user has exceeded maximum attempts
        Exception: Any grading errors are logged and re-raised
    """
    # Get assessment ID
    selector = AssessmentSelector(resource_context=resource_context)
    assessment_id = await selector.get_assessment_id()

    # Extract context data
    user_id = resource_context.resources.user.id
    question_id = resource_context.validated_data["question_id"]
    collection_name = resource_context.resources.collection_name

    logger.info(
        "Starting grading workflow for assessment_id=%s, user_id=%s, question_id=%s",
        assessment_id,
        user_id,
        question_id,
    )
    # Step 1: Prepare grading data
    target_question, previous_attempt = await prepare_grading_data(
        question_id=question_id,
        user_id=user_id,
        assessment_id=assessment_id,
        resource_context=resource_context,
    )

    # Step 2: Check attempt limits
    if previous_attempt and previous_attempt.total_attempts >= 3:
        raise MaximumAttemptsExceededError(
            user_id=user_id, question_id=question_id, max_attempts=3
        )

    # Step 3: Prepare student answer
    submitted_answer = StudentAnswer(
        question_type=resource_context.validated_data["question_type"],
        question_metadata=resource_context.validated_data["question_metadata"],
    )

    # Step 4: Execute grading
    result = await execute_grading(
        target_question=target_question,
        previous_attempt=previous_attempt,
        user_id=user_id,
        submitted_answer=submitted_answer,
    )

    # Step 5: Save results if not already mastered
    if not previous_attempt or not previous_attempt.mastered:
        await save_grading_results(
            result=result,
            target_question=target_question,
            previous_attempt=previous_attempt,
            user_id=user_id,
            assessment_id=assessment_id,
            collection_name=collection_name,
        )

    logger.info(
        "Successfully completed grading workflow for assessment_id=%s, score=%s",
        assessment_id,
        getattr(result, "score", "unknown"),
    )

    return result
