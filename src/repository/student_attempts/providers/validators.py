from typing import Optional

from src.repository.question_repository.data_types import Question
from src.repository.question_repository.exceptions import QuestionAttemptError

from ..data_types import StudentQuestionAttempt
from .data_types import GradingConfig


class AttemptValidationService:
    """Handles validation logic for student attempts"""

    def __init__(self, config: GradingConfig):
        self.config = config

    @staticmethod
    def validate_attempt_inputs(user_id: str, question: Question, score: float) -> None:
        """Validate basic attempt inputs"""
        if not user_id or not question or not question.id:
            raise QuestionAttemptError("User ID and valid Question are required")

        if score < 0 or score > 1:
            raise QuestionAttemptError(
                f"Invalid score: {score}. Score must be between 0 and 1"
            )

    def validate_attempt_limits(
        self, question_attempt: Optional[StudentQuestionAttempt], question_id: str
    ) -> None:
        """Check if attempt limits have been exceeded"""
        if (
            self.config.max_attempts
            and question_attempt
            and question_attempt.total_attempts >= self.config.max_attempts
        ):
            raise QuestionAttemptError(
                f"Maximum attempts ({self.config.max_attempts}) exceeded for question {question_id}"
            )

    @staticmethod
    def validate_retrieval_inputs(user_id: str, question_id: str) -> None:
        """Validate inputs for attempt retrieval"""
        if not user_id or not question_id:
            raise QuestionAttemptError("User ID and Question ID are required")
