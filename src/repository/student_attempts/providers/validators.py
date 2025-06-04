from typing import Optional

from src.exceptions import (
    InvalidAttemptInputError,
    InvalidScoreError,
    MaximumAttemptsExceededError,
)
from src.repository.question_repository.data_types import Question

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
            raise InvalidAttemptInputError(
                missing_field="user_id , question_id and question are required",
            )

        # TODO : dont hardcode numbers
        if score < 0 or score > 1:
            raise InvalidScoreError(
                score=score,
                min_score=0,
                max_score=1,
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
            # TODO : dont hardcode numbers
            raise MaximumAttemptsExceededError(
                user_id=question_attempt.user_id,
                question_id=question_attempt.question_id,
                max_attempts=3,
                current_attempts=question_attempt.total_attempts,
            )

    @staticmethod
    def validate_retrieval_inputs(user_id: str, question_id: str) -> None:
        """Validate inputs for attempt retrieval"""
        if not user_id or not question_id:
            raise InvalidAttemptInputError(
                missing_field="user_id and question_id are required",
            )

    def __repr__(self):
        return f"<{type(self).__name__}: {self.config!r}>"
