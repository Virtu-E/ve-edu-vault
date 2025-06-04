import logging
from datetime import datetime
from typing import Optional, Type

from src.repository.graded_responses.data_types import (
    GradedFeedback,
    GradedResponse,
    StudentAnswer,
)
from src.repository.question_repository.data_types import Question
from src.repository.student_attempts.data_types import StudentQuestionAttempt

from .grader_factory import GraderFactory

logger = logging.getLogger(__name__)


class SingleQuestionGrader:
    """
    Grades individual student question attempts with feedback and attempt tracking.

    Manages the complete grading workflow including attempt validation,
    scoring, feedback generation, and mastery tracking.
    """

    MASTERY_SCORE_THRESHOLD = 1.0
    DEFAULT_MAXIMUM_ATTEMPTS_ALLOWED = 3

    def __init__(
        self,
        maximum_attempts_per_question: int = DEFAULT_MAXIMUM_ATTEMPTS_ALLOWED,
        question_grader_factory: Type[GraderFactory] = GraderFactory,
    ) -> None:
        """
        Initialize grading engine with attempt limits and grader factory.

        Args:
            maximum_attempts_per_question: Max attempts allowed per question
            question_grader_factory: Factory for creating question-type specific graders
        """
        self.question_grader_factory = question_grader_factory
        self.maximum_attempts_per_question = maximum_attempts_per_question
        logger.info(
            f"SingleQuestionGrader initialized with max_attempts: {maximum_attempts_per_question}"
        )

    def grade(
        self,
        student_user_id: str,
        submitted_answer: StudentAnswer,
        target_question: Question,
        previous_attempt_history: Optional[StudentQuestionAttempt],
    ) -> GradedResponse:
        """
        Grade a student's answer attempt and generate comprehensive feedback.

        Args:
            student_user_id: Student's unique identifier
            submitted_answer: The student's submitted answer
            target_question: Question being attempted
            previous_attempt_history: Prior attempt data if exists

        Returns:
            Complete grading response with score, feedback, and attempt tracking
        """
        current_attempt_number = self._calculate_current_attempt_number(
            previous_attempt_history
        )
        logger.debug(
            f"Evaluating attempt #{current_attempt_number} for user: {student_user_id}, question: {target_question.id}"
        )

        # Handle special cases first
        special_case_response = self._handle_special_grading_cases(
            target_question,
            previous_attempt_history,
            submitted_answer,
            student_user_id,
        )
        if special_case_response:
            return special_case_response

        # Perform actual grading
        question_type_grader = self.question_grader_factory.get_grader(
            target_question.question_type
        )
        answer_is_correct = question_type_grader.grade(
            target_question, submitted_answer
        )
        calculated_score = question_type_grader.calculate_score(answer_is_correct)

        remaining_attempts_count = max(
            0, self.maximum_attempts_per_question - current_attempt_number
        )

        comprehensive_feedback = self._generate_contextual_feedback(
            remaining_attempts=remaining_attempts_count,
            question=target_question,
            answer_is_correct=answer_is_correct,
        )

        logger.info(
            f"Graded question {target_question.id} for user {student_user_id}: "
            f"correct={answer_is_correct}, score={calculated_score}, attempts_remaining={remaining_attempts_count}"
        )

        return GradedResponse(
            is_correct=answer_is_correct,
            question_id=target_question.id,
            user_id=int(student_user_id),
            grading_version="1.0",
            created_at=datetime.now(),
            score=calculated_score,
            feedback=comprehensive_feedback,
            attempts_remaining=remaining_attempts_count,
            question_metadata=submitted_answer.question_metadata,
            question_type=target_question.question_type,
        )

    def _generate_contextual_feedback(
        self,
        remaining_attempts: int,
        question: Question,
        answer_is_correct: bool,
    ) -> GradedFeedback:
        """
        Create appropriate feedback based on correctness and attempt history.

        Args:
            remaining_attempts: Number of attempts left
            question: Question being attempted
            answer_is_correct: Whether current answer is correct

        Returns:
            Structured feedback with messages, hints, and solution details
        """
        attempts_used = self.maximum_attempts_per_question - remaining_attempts

        if answer_is_correct:
            success_feedback = GradedFeedback(
                message=self._create_success_message_for_attempt(attempts_used),
                explanation=question.solution.explanation,
                steps=question.solution.steps,
                show_solution=True,
            )
            return success_feedback

        # No attempts remaining - show full solution
        if remaining_attempts <= 0:
            final_attempt_feedback = GradedFeedback(
                message="You've used all your attempts. Here's the complete solution:",
                explanation=question.solution.explanation,
                steps=question.solution.steps,
                show_solution=True,
            )

            # Add misconception info if available
            if (
                hasattr(question, "possible_misconception")
                and question.possible_misconception
            ):
                final_attempt_feedback.misconception = question.possible_misconception

            return final_attempt_feedback

        # Progressive hints for incorrect answers with attempts remaining
        progressive_feedback = GradedFeedback(message="", show_solution=False)
        if attempts_used == 1:
            progressive_feedback.message = "Not quite right. Let's try again!"

        elif attempts_used == 2:
            progressive_feedback.message = "Getting closer! Here's a hint:"

            if hasattr(question, "hint") and question.hint:
                progressive_feedback.hint = f"{question.hint}"
            else:
                progressive_feedback.hint = (
                    "Review the question carefully and consider all options."
                )

        return progressive_feedback

    @staticmethod
    def _create_success_message_for_attempt(attempts_used_count: int) -> str:
        """
        Generate encouraging success message based on attempt count.

        Args:
            attempts_used_count: Number of attempts student has made

        Returns:
            Contextual congratulatory message
        """
        if attempts_used_count == 1:
            return "Excellent! You got it right on your first try!"
        elif attempts_used_count == 2:
            return "Great job! You figured it out on your second attempt."
        else:
            return "Well done! You've mastered this question."

    @staticmethod
    def _calculate_current_attempt_number(
        attempt_history: Optional[StudentQuestionAttempt],
    ) -> int:
        """
        Determine the current attempt number for this question.

        Args:
            attempt_history: Previous attempt data if exists

        Returns:
            Current attempt number (1-based indexing)
        """
        if not attempt_history:
            return 1
        return attempt_history.total_attempts + 1

    def _student_has_exceeded_attempt_limit(
        self, attempt_history: Optional[StudentQuestionAttempt]
    ) -> bool:
        """
        Check if student has reached maximum allowed attempts.

        Args:
            attempt_history: Previous attempt data if exists

        Returns:
            True if maximum attempts reached or exceeded, False otherwise
        """
        return (
            attempt_history is not None
            and attempt_history.total_attempts >= self.maximum_attempts_per_question
        )

    def _handle_special_grading_cases(
        self,
        target_question: Question,
        attempt_history: Optional[StudentQuestionAttempt],
        submitted_answer: StudentAnswer,
        student_user_id: str,
    ) -> Optional[GradedResponse]:
        """
        Handle edge cases that bypass normal grading flow.

        Args:
            target_question: Question being attempted
            attempt_history: Previous attempt data if exists
            submitted_answer: Student's submitted answer
            student_user_id: Student's unique identifier

        Returns:
            GradedResponse for special cases, None for normal flow
        """
        # Already mastered question
        if attempt_history and getattr(attempt_history, "mastered", False):
            logger.info(
                f"Question {target_question.id} already mastered by student, returning mastery response"
            )

            mastery_feedback = GradedFeedback(
                message="You've already mastered this question!",
                explanation=target_question.solution.explanation,
                steps=target_question.solution.steps,
                show_solution=True,
            )

            remaining_attempts = max(
                0, self.maximum_attempts_per_question - attempt_history.total_attempts
            )

            return GradedResponse(
                question_id=target_question.id,
                user_id=int(student_user_id),
                grading_version="1.0",
                created_at=datetime.now(),
                is_correct=True,
                score=getattr(attempt_history, "best_score", 1.0),
                feedback=mastery_feedback,
                attempts_remaining=remaining_attempts,
                question_metadata=submitted_answer.question_metadata,
                question_type=target_question.question_type,
            )

        # Maximum attempts exceeded
        if self._student_has_exceeded_attempt_limit(attempt_history):
            logger.warning(
                f"Maximum attempts exceeded for question {target_question.id}, attempts: {attempt_history.total_attempts}"
            )

            exceeded_attempts_feedback = self._generate_contextual_feedback(
                remaining_attempts=0,
                question=target_question,
                answer_is_correct=False,
            )

            return GradedResponse(
                question_id=target_question.id,
                user_id=int(student_user_id),
                grading_version="1.0",
                created_at=datetime.now(),
                is_correct=False,
                score=0,
                feedback=exceeded_attempts_feedback,
                attempts_remaining=0,
                question_metadata=submitted_answer.question_metadata,
                question_type=target_question.question_type,
            )

        return None

    def __repr__(self):
        return f"<{type(self).__name__}: {self.maximum_attempts_per_question}, {self.question_grader_factory!r}>"
