from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from src.repository.question_repository.data_types import Question
from src.repository.student_attempts.data_types import StudentQuestionAttempt


@dataclass
class GradingConfig:
    mastery_threshold: float = 1.0
    max_attempts: Optional[int] = 3
    enable_partial_credit: bool = True
    timeout_seconds: Optional[int] = None


@dataclass
class AttemptBuildContext:
    user_id: str
    question: Question
    is_correct: bool
    score: float
    existing_attempt: Optional[StudentQuestionAttempt]
    config: GradingConfig


class BulkAttemptBuildContext:
    """Context for building bulk attempt data for unanswered questions"""

    def __init__(
        self,
        user_id: str,
        unanswered_questions: List[Question],
        assessment_id: UUID,
        config=None,  # GradingConfig
        default_score: float = 0.0,
        is_correct: bool = False,
    ):
        self.user_id = user_id
        self.unanswered_questions = unanswered_questions
        self.assessment_id = assessment_id
        self.config = config
        self.default_score = default_score
        self.is_correct = is_correct
