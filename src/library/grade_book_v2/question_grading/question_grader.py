import logging
from typing import Optional, Type

from src.repository.grading_repository.base_grading_repository import (
    AbstractGradingRepository,
)
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt
from src.repository.grading_repository.mongo_grading_repository import (
    MongoGradingRepository,
)
from src.repository.question_repository.qn_repository_data_types import Question

from .data_types import AttemptedAnswer, Feedback, GradingResponse
from .grader_factory import GraderFactory

logger = logging.getLogger(__name__)


class SingleQuestionGrader:
    """
    Service for handling the grading of student question attempts.

    This service manages the grading process for various question types,
    tracks student attempts, provides appropriate feedback based on performance,
    and handles the persistence of attempt data.

    Attributes:
        repository: Repository interface for storing and retrieving grading data
        grader: Factory for creating question-type specific graders
        max_attempts: Maximum number of attempts allowed per question
    """

    MASTERY_THRESHOLD = 1.0
    DEFAULT_MAX_ATTEMPTS = 3

    def __init__(
        self,
        grading_repository: AbstractGradingRepository,
        collection_name: str,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        grading_factory: Type[GraderFactory] = GraderFactory,
    ) -> None:
        """
        Initialize the GradingService with repository and configuration.

        Args:
            grading_repository: The grading repository for data access
            collection_name: Name of the collection to use
            max_attempts: Maximum number of attempts allowed per question (default: 3)
            grading_factory: Factory class for creating appropriate graders (default: GraderFactory)
        """
        self.grading_repository = grading_repository
        self.grader = grading_factory
        self.max_attempts = max_attempts
        self.collection_name = collection_name
        logger.info(
            f"SingleQuestionGrader initialized with collection: {collection_name}, max_attempts: {max_attempts}"
        )

    def grade(
        self,
        user_id: str,
        attempted_answer: AttemptedAnswer,
        question: Question,
        question_attempt: Optional[StudentQuestionAttempt],
    ) -> GradingResponse:
        """
        Process the grading for a question attempt without saving to the database.

        Args:
            user_id: Unique identifier for the student
            attempted_answer: The student's answer
            question: The question being attempted
            question_attempt: Previous attempt data if exists

        Returns:
            GradingResponse with the results
        """
        # Calculate attempt count based on question_attempt
        attempt_count = self._get_attempt_count(question_attempt)
        logger.debug(
            f"Grading attempt #{attempt_count} for user: {user_id}, question: {question.id}"
        )

        # Check for special cases
        special_response = self._check_special_cases(
            question,
            question_attempt,
            attempted_answer,
        )
        if special_response:
            return special_response

        # Perform grading
        grader = self.grader.get_grader(question.question_type)
        is_correct = grader.grade(question, attempted_answer)
        score = grader.calculate_score(is_correct)

        attempts_remaining = max(0, self.max_attempts - attempt_count)

        grading_feedback = self._get_grading_feedback(
            attempts_remaining=attempts_remaining,
            question=question,
            is_correct=is_correct,
        )

        logger.info(
            f"Graded question {question.id} for user {user_id}: "
            f"correct={is_correct}, score={score}, attempts_remaining={attempts_remaining}"
        )

        return GradingResponse(
            success=True,
            is_correct=is_correct,
            score=score,
            feedback=grading_feedback,
            attempts_remaining=attempts_remaining,
            question_metadata=attempted_answer.question_metadata,
            question_type=question.question_type,
        )

    def _get_grading_feedback(
        self,
        attempts_remaining: int,
        question: Question,
        is_correct: bool,
    ) -> Feedback:
        """
        Generate comprehensive feedback based on the student's performance and attempt history.

        Args:
            attempts_remaining: Number of attempts remaining
            question: The question being attempted
            is_correct: Whether the current answer is correct

        Returns:
            Feedback object with structured feedback that can be used flexibly in responses
        """
        attempts_made = self.max_attempts - attempts_remaining

        if is_correct:
            feedback = Feedback(
                message=self._get_success_message(attempts_made),
                explanation=question.solution.explanation,
                steps=question.solution.steps,
                show_solution=True,
            )
            return feedback

        # When no attempts remaining
        if attempts_remaining <= 0:
            feedback = Feedback(
                message="You've used all your attempts. Here's the complete solution:",
                explanation=question.solution.explanation,
                steps=question.solution.steps,
                show_solution=True,
            )

            # Safely check for misconception
            if (
                hasattr(question, "possible_misconception")
                and question.possible_misconception
            ):
                feedback.misconception = question.possible_misconception

            return feedback

        # Progressive hints based on attempts
        feedback = Feedback(message="")
        if attempts_made == 1:
            feedback.message = "Not quite right. Let's try again!"

        elif attempts_made == 2:
            feedback.message = "Getting closer! Here's a hint:"

            if hasattr(question, "hint") and question.hint:
                feedback.hint = f"{question.hint}"
            else:
                feedback.hint = (
                    "Review the question carefully and consider all options."
                )

        return feedback

    @staticmethod
    def _get_success_message(attempts_made: int) -> str:
        """
        Generate a contextual success message based on attempt count.

        Args:
            attempts_made: Number of attempts the student has made

        Returns:
            A congratulatory message customized to the number of attempts
        """
        if attempts_made == 1:
            return "Excellent! You got it right on your first try!"
        elif attempts_made == 2:
            return "Great job! You figured it out on your second attempt."
        else:
            return "Well done! You've mastered this question."

    @staticmethod
    def _get_attempt_count(question_attempt: Optional[StudentQuestionAttempt]) -> int:
        """
        Get the current attempt number for the student on this question.

        Args:
            question_attempt: Previous attempt data if exists

        Returns:
            Integer representing the current attempt number (1-based)
        """
        if not question_attempt:
            return 1
        return question_attempt.total_attempts + 1

    def _has_exceeded_max_attempts(
        self, question_attempt: Optional[StudentQuestionAttempt]
    ) -> bool:
        """
        Check if user has exceeded maximum attempts for this question.

        Args:
            question_attempt: Previous attempt data if exists

        Returns:
            True if the user has reached or exceeded the maximum allowed attempts,
            False otherwise or if no previous attempts exist
        """
        return (
            question_attempt is not None
            and question_attempt.total_attempts >= self.max_attempts
        )

    def _check_special_cases(
        self,
        question: Question,
        question_attempt: Optional[StudentQuestionAttempt],
        attempted_answer: AttemptedAnswer,
    ) -> Optional[GradingResponse]:
        """
        Check for special cases that might short-circuit the normal grading flow.

        Args:
            question: The question being attempted
            question_attempt: Previous attempt data if exists

        Returns:
            GradingResponse if a special case applies, None otherwise
        """
        # Check if question is already mastered
        if question_attempt and getattr(question_attempt, "mastered", False):
            logger.info(
                f"Question {question.id} already mastered by student, returning preemptive response"
            )

            feedback = Feedback(
                message="You've already mastered this question!",
                explanation=question.solution.explanation,
                steps=question.solution.steps,
                show_solution=True,
            )

            attempts_remaining = max(
                0, self.max_attempts - question_attempt.total_attempts
            )

            return GradingResponse(
                success=False,  # already mastered, grading did not happen again
                is_correct=True,  # Always true since it's mastered
                score=getattr(question_attempt, "best_score", 1.0),
                feedback=feedback,
                attempts_remaining=attempts_remaining,
                question_metadata=attempted_answer.question_metadata,
                question_type=question.question_type,
            )

        # Check if max attempts exceeded BEFORE grading
        if self._has_exceeded_max_attempts(question_attempt):
            logger.warning(
                f"Maximum attempts exceeded for question {question.id}, attempts: {question_attempt.total_attempts}"
            )

            grading_feedback = self._get_grading_feedback(
                attempts_remaining=0,
                question=question,
                is_correct=False,  # We assume incorrect since we're out of attempts
            )

            return GradingResponse(
                success=False,  # maximum attempt reached, grading did not happen
                is_correct=False,
                score=0,
                feedback=grading_feedback,
                attempts_remaining=0,
                question_metadata=attempted_answer.question_metadata,
                question_type=question.question_type,
            )

        return None

    @classmethod
    def get_grader(cls, collection_name: str) -> "SingleQuestionGrader":
        """
        Factory method to create a SingleQuestionGrader instance.

        Args:
            collection_name: Name of the collection to use

        Returns:
            SingleQuestionGrader instance
        """
        logger.info(
            f"Creating new SingleQuestionGrader with collection: {collection_name}"
        )
        return cls(
            grading_repository=MongoGradingRepository.get_repo(),
            collection_name=collection_name,
        )
