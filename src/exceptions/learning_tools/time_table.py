from typing import Optional

from src.exceptions import VirtuEducateValidationError


class TaskValidationError(VirtuEducateValidationError): ...


class PastDateError(TaskValidationError):
    """Raised when a task is scheduled for a past date/time."""

    def __init__(
        self,
        message: str = "Cannot schedule task for a past date/time",
        error_code: str = "TASK_PAST_DATE",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)


class TaskAlreadyCompletedError(TaskValidationError):
    """Raised when attempting to modify a task that is already completed."""

    def __init__(
        self,
        message: str = "Task is already completed and cannot be modified",
        error_code: str = "TASK_ALREADY_COMPLETED",
        context: Optional[dict] = None,
        *args,
    ):
        super().__init__(message, error_code, context, *args)
