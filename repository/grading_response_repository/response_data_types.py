from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Feedback(BaseModel):
    """
    Contains feedback information for a question attempt.

    Attributes:
        message (str): A brief feedback message.
        explanation (str): A detailed explanation of the answer.
        steps (List[str]): Step-by-step breakdown of the solution.
        hint (Optional[str]): An optional hint for the user.
        show_solution (bool): Whether to display the complete solution.
        misconception (Optional[str]): Common misconception related to the question.
    """

    message: str
    explanation: Optional[str] = None
    steps: Optional[List[str]] = None
    hint: Optional[str] = None
    show_solution: bool
    misconception: Optional[str] = None


class QuestionAttempt(BaseModel):
    """
    Represents a user's attempt at answering a question.

    Attributes:
        question_id (str): Unique identifier for the question.
        user_id (int): Identifier for the user making the attempt.
        attempts_remaining (int): Number of attempts remaining for the user.
        created_at (datetime): Timestamp when the attempt was created.
        feedback (Feedback): Feedback provided for this attempt.
        grading_version (str): Version of the grading system used.
        is_correct (bool): Whether the attempt was correct.
        question_metadata: Metadata about the question attempt.
        question_type (str): Type of question (e.g., "multiple-choice").
        score (float): Score awarded for this attempt.
    """

    question_id: str
    user_id: int
    attempts_remaining: int
    created_at: datetime
    feedback: Feedback
    grading_version: str
    is_correct: bool
    question_metadata: Dict[str, Any]
    question_type: str
    score: float

    class Config:
        """Configuration for the QuestionAttempt model."""

        populate_by_name = True
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%SZ")}
