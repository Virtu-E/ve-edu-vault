import asyncio
import logging
from typing import Optional, Tuple
from uuid import UUID

from src.apps.learning_tools.questions.services.graded_responses import (
    save_graded_response,
)
from src.exceptions import QuestionNotFoundError
from src.library.grade_book_v2.question_grading.question_grader import (
    SingleQuestionGrader,
)
from src.repository.graded_responses.data_types import GradedResponse, StudentAnswer
from src.repository.question_repository.data_types import Question
from src.repository.question_repository.providers.question_provider import (
    QuestionProvider,
)
from src.repository.student_attempts.data_types import StudentQuestionAttempt
from src.repository.student_attempts.providers.factories import (
    StudentAttemptProviderFactory,
)
from src.utils.mixins.question_mixin import QuestionSetResources

logger = logging.getLogger(__name__)


async def prepare_grading_data(
    question_id: str,
    user_id: str,
    assessment_id: UUID,
    resource_context: QuestionSetResources,
) -> Tuple[Question, Optional[StudentQuestionAttempt]]:
    """
    Prepare data needed for grading by fetching question and attempt history.

    Args:
        question_id: ID of the question to grade
        user_id: ID of the student
        assessment_id: ID of the assessment
        resource_context: Resources containing context information

    Returns:
        Tuple of (target_question, previous_attempt)
    """
    logger.debug(
        "Preparing grading data for question_id=%s, user_id=%s, assessment_id=%s",
        question_id,
        user_id,
        assessment_id,
    )

    question_provider = QuestionProvider.get_mongo_provider(resource_context)
    attempt_provider = StudentAttemptProviderFactory.create_mongo_attempt_provider(
        resource_context.resources.collection_name
    )

    target_question, previous_attempt = await asyncio.gather(
        question_provider.get_question_by_id(question_id),
        attempt_provider.get_question_attempt(
            student_user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
        ),
    )
    if not target_question:
        raise QuestionNotFoundError(
            question_id=question_id,
            user_id=user_id,
            collection=resource_context.resources.collection_name,
        )

    logger.debug(
        "Retrieved question (found=%s) and previous attempt (found=%s)",
        target_question is not None,
        previous_attempt is not None,
    )

    return target_question, previous_attempt


async def execute_grading(
    target_question: Question,
    previous_attempt: Optional[StudentQuestionAttempt],
    user_id: str,
    submitted_answer: StudentAnswer,
) -> GradedResponse:
    """
    Execute the grading logic using the SingleQuestionGrader.

    Args:
        target_question: The question being graded
        previous_attempt: Previous attempt history (if any)
        user_id: ID of the student
        submitted_answer: The student's submitted answer

    Returns:
        GradedResponse: The graded result
    """
    logger.debug(
        "Executing grading for user_id=%s, question_id=%s", user_id, target_question.id
    )

    grader = SingleQuestionGrader()
    result = grader.grade(
        target_question=target_question,
        previous_attempt_history=previous_attempt,
        student_user_id=user_id,
        submitted_answer=submitted_answer,
    )

    logger.debug(
        "Grading completed for user_id=%s, question_id=%s, score=%s",
        user_id,
        target_question.id,
        getattr(result, "score", "unknown"),
    )

    return result


async def save_grading_results(
    result: GradedResponse,
    target_question: Question,
    previous_attempt: Optional[StudentQuestionAttempt],
    user_id: str,
    assessment_id: UUID,
    collection_name: str,
) -> None:
    """
    Save grading results to the database.

    Args:
        result: The graded response to save
        target_question: The question that was graded
        previous_attempt: Previous attempt history (if any)
        user_id: ID of the student
        assessment_id: ID of the assessment
        collection_name: Name of the collection for data storage
    """
    logger.debug(
        "Saving grading results for user_id=%s, assessment_id=%s",
        user_id,
        assessment_id,
    )

    attempt_provider = StudentAttemptProviderFactory.create_mongo_attempt_provider(
        collection_name
    )

    await asyncio.gather(
        save_graded_response(
            graded_response=result,
            assessment_id=assessment_id,
            user_id=user_id,
            collection_name=collection_name,
        ),
        attempt_provider.save_attempt(
            student_user_id=user_id,
            question=target_question,
            assessment_id=assessment_id,
            is_answer_correct=result.is_correct,
            attempt_score=result.score,
            existing_attempt=previous_attempt,
        ),
    )

    logger.debug(
        "Successfully saved grading results for user_id=%s, assessment_id=%s",
        user_id,
        assessment_id,
    )
