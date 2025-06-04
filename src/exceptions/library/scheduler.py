from typing import Optional

from src.exceptions import VirtuEducateSystemError


class SchedulingError(VirtuEducateSystemError):
    """Assessment scheduling operation failed"""

    def __init__(
        self,
        message: str = "Failed to schedule assessment",
        assessment_id: Optional[str] = None,
        student_id: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        qstash_error: Optional[str] = None,
        webhook_url: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)

        self.error_code = "500"

        self.context = {
            k: v
            for k, v in {
                "assessment_id": assessment_id,
                "student_id": student_id,
                "duration_seconds": duration_seconds,
                "qstash_error": qstash_error,
                "webhook_url": webhook_url,
                "error_type": "SCHEDULING_FAILED",
            }.items()
            if v is not None
        }
