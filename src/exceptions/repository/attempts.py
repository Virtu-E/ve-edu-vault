from typing import Optional, Union

from src.exceptions import (VirtuEducateBusinessError,
                            VirtuEducateValidationError)


class MaximumAttemptsExceededError(VirtuEducateBusinessError):
    """User has reached maximum attempts for a question"""

    def __init__(
        self,
        user_id: Union[str, int],
        question_id: str,
        max_attempts: int,
        current_attempts: Optional[int] = None,
        **kwargs,
    ):
        message = f"User {user_id} exceeded maximum attempts ({max_attempts}) for question {question_id}"
        super().__init__(message, **kwargs)

        self.context = {
            k: v
            for k, v in {
                "user_id": user_id,
                "question_id": question_id,
                "max_attempts": max_attempts,
                "error_type": "MAX_ATTEMPTS_EXCEEDED",
            }.items()
            if v is not None
        }
        self.error_code = "422"


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
        self.error_code = "400"
        self.context = {
            "error_type": "INVALID_ATTEMPT_INPUT",
        }


class InvalidScoreError(VirtuEducateValidationError):
    """Score value is outside valid range"""

    def __init__(self, score: float, min_score: float, max_score: float, **kwargs):
        message = (
            f"Invalid score: {score}. Score must be between {min_score} and {max_score}"
        )
        super().__init__(message, **kwargs)

        self.error_code = "400"

        self.context = {
            "error_code": self.error_code,
            "score": score,
            "min_score": min_score,
            "max_score": max_score,
            "error_type": "INVALID_SCORE",
        }
