from typing import Optional, Union

from src.exceptions import VirtuEducateBusinessError, VirtuEducateValidationError


class MaximumAttemptsExceededError(VirtuEducateBusinessError):
    """User has reached maximum attempts for a question"""

    def __init__(
        self,
        user_id: Union[str, int],
        question_id: str,
        max_attempts: int,
        current_attempts: int,
        **kwargs,
    ):
        message = f"User {user_id} exceeded maximum attempts ({max_attempts}) for question {question_id}"
        super().__init__(message, **kwargs)

        self.user_id = user_id
        self.question_id = question_id
        self.max_attempts = max_attempts
        self.current_attempts = current_attempts
        self.error_code = "MAX_ATTEMPTS_EXCEEDED"


class InvalidAttemptInputError(VirtuEducateValidationError):
    """Invalid input provided for student attempt"""

    def __init__(
        self,
        missing_field: Optional[str] = None,
        invalid_value: Optional[str] = None,
        **kwargs,
    ):
        message = "Invalid attempt input"
        if missing_field:
            message += f" - missing: {missing_field}"
        if invalid_value:
            message += f" - invalid: {invalid_value}"

        super().__init__(message, **kwargs)
        self.error_code = "INVALID_ATTEMPT_INPUT"


class InvalidScoreError(VirtuEducateValidationError):
    """Score value is outside valid range"""

    def __init__(self, score: float, min_score: float, max_score: float, **kwargs):
        message = (
            f"Invalid score: {score}. Score must be between {min_score} and {max_score}"
        )
        super().__init__(message, **kwargs)

        self.score = score
        self.min_score = min_score
        self.max_score = max_score
        self.error_code = "INVALID_SCORE"

        self.context = {
            "error_code": self.error_code,
            "score": score,
            "min_score": min_score,
            "max_score": max_score,
            "error_type": "validation",
        }
