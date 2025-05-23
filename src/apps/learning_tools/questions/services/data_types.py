from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.library.grade_book_v2.question_grading.data_types import GradingResponse
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt
from src.repository.question_repository.qn_repository_data_types import Question


@dataclass
class GradingConfig:
    mastery_threshold: float = 1.0
    max_attempts: Optional[int] = 3
    enable_partial_credit: bool = True
    timeout_seconds: Optional[int] = None


@dataclass
class AssessmentContext:
    user_id: str
    question_id: str
    collection_name: str
    assessment_id: Optional[UUID] = None


@dataclass
class AttemptContext:
    user_id: str
    question: Question
    question_id: str
    assessment_id: UUID
    question_attempt: Optional[StudentQuestionAttempt]
    grading_result: GradingResponse
    config: GradingConfig


@dataclass
class AttemptBuildContext:
    user_id: str
    question: Question
    is_correct: bool
    score: float
    existing_attempt: Optional[StudentQuestionAttempt]
    config: GradingConfig


@dataclass
class ServiceDependencies:
    """Groups all service dependencies"""

    assessment_service: "AssessmentService"
    question_service: "QuestionService"
    grader_factory: "GraderFactory"
    grading_service: "GradingService"
    attempt_saving_service: "AttemptSavingService"
    question_attempt_service: "QuestionAttemptService"


@dataclass
class RecordQuestionAttemptResponse:
    question_id: str
    grading_result: GradingResponse
    success: bool
    timestamp: Optional[str] = None

    @classmethod
    def success_response(
        cls, question_id: str, grading_result: GradingResponse
    ) -> "RecordQuestionAttemptResponse":
        from datetime import datetime

        return cls(
            question_id=question_id,
            grading_result=grading_result,
            success=True,
            timestamp=datetime.utcnow().isoformat(),
        )

    @classmethod
    def failure_response(
        cls, question_id: str, grading_result: GradingResponse
    ) -> "RecordQuestionAttemptResponse":
        from datetime import datetime

        return cls(
            question_id=question_id,
            grading_result=grading_result,
            success=False,
            timestamp=datetime.utcnow().isoformat(),
        )
