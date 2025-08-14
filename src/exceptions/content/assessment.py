from typing import Optional

from src.exceptions import VirtuEducateValidationError


class AssessmentValidationError(VirtuEducateValidationError): ...


class NoActiveAssessmentError(AssessmentValidationError):
    """Raised when a student submits a question for grading but has no active assessment."""

    def __init__(
        self,
        message: str = "No active assessment found for this student",
        error_code: str = "NO_ACTIVE_ASSESSMENT",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)


class AssessmentAlreadyGradedError(AssessmentValidationError):
    """Raised when a student tries to submit an assessment that has already been graded."""

    def __init__(
        self,
        message: str = "Assessment already graded",
        error_code: str = "ASSESSMENT_ALREADY_GRADED",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)
