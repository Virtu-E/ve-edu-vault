from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer


@dataclass
class AssessmentConfig:
    """Configuration for assessment grading."""

    passing_threshold: float = 0.8
    max_attempts_per_question: int = 3
    enable_partial_credit: bool = False
    auto_submit_on_completion: bool = True


@dataclass
class QuestionAttemptSummary:
    """Summary of a single question attempt."""

    question_id: str
    attempted: bool
    is_correct: bool
    score: float
    total_attempts: int
    mastered: bool
    best_score: float
    latest_score: float


class AssessmentResult(BaseModel):
    """Result of assessment grading."""

    assessment_id: str
    user_id: int
    learning_objective_id: int
    total_questions: int
    attempted_questions: int
    correct_questions: int
    incorrect_questions: int
    unattempted_questions: int
    overall_score: float
    passing_threshold: float
    passed: bool
    completion_percentage: float
    graded_at: datetime
    question_summaries: List[QuestionAttemptSummary]

    @field_serializer("graded_at")
    def serialize_dt(self, graded_at: datetime, _info):
        return graded_at.isoformat()


@dataclass
class AssessmentGradingRequest:
    """Request data for assessment grading."""

    assessment_id: UUID
    user_id: str
    learning_objective_id: str
    config: Optional[AssessmentConfig] = None
