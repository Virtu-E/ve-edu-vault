"""
Notify the user about his grading results
"""

from course_ware.models import EdxUser
from data_types.ai_core import EvaluationResult
from grade_book.evaluation_observers.base_observer import EvaluationObserver


class EmailNotificationObserver(EvaluationObserver):
    def __init__(self, user: EdxUser):
        self._user = user

    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        # Send email notification about the evaluation result
        if evaluation_result.passed:
            pass
            # send_congratulation_email(self._user)
        else:
            pass
            # send_encouragement_email(self._user)
