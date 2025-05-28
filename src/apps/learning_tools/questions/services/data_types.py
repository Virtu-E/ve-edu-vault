from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from src.repository.graded_responses.data_types import StudentAnswer
from src.repository.question_repository.data_types import Question
from src.repository.student_attempts.data_types import StudentQuestionAttempt


@dataclass
class AssessmentContext:
    user_id: str
    question_id: str
    collection_name: str
    submitted_answer: StudentAnswer
    assessment_id: UUID


@dataclass
class GradingContext:
    student_user_id: str
    submitted_answer: StudentAnswer
    target_question: Question
    previous_attempt_history: Optional[StudentQuestionAttempt]

    @property
    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_user_id": self.student_user_id,
            "submitted_answer": self.submitted_answer,
            "target_question": self.target_question,
            "previous_attempt_history": self.previous_attempt_history,
        }
