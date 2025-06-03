import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from src.apps.core.content.models import LearningObjective
from src.apps.core.users.models import EdxUser
from src.repository.student_attempts.data_types import StudentQuestionAttempt

from .data_types import AssessmentConfig, AssessmentResult, QuestionAttemptSummary

logger = logging.getLogger(__name__)


class AssessmentGrader:
    """Grades complete assessments by evaluating student performance across all questions."""

    def __init__(
        self,
        user: EdxUser,
        learning_objective: LearningObjective,
        assessment_id: UUID,
        config: Optional[AssessmentConfig] = None,
    ):
        self._user = user
        self._assessment_id = assessment_id
        self._learning_objective = learning_objective
        self._config = config or AssessmentConfig()

        logger.info(
            f"AssessmentGrader initialized "
            f"threshold: {self._config.passing_threshold}"
        )

    async def grade_assessment(
        self, attempts: List[StudentQuestionAttempt]
    ) -> AssessmentResult:
        """
        Grade a complete assessment for a user.

        Args:
            attempts: List of student question attempts

        Returns:
            Complete assessment grading results
        """
        logger.info(
            f"Starting assessment grading for user {self._user.username}, "
            f"assessment {self._assessment_id}"
        )

        result = self._build_assessment_result(attempts)

        logger.info(
            f"Assessment grading completed for user {self._user.username}: "
            f"Score: {result.overall_score:.2%}, Passed: {result.passed}"
        )

        return result

    def _build_assessment_result(
        self, attempts: List[StudentQuestionAttempt]
    ) -> AssessmentResult:
        """Build the final assessment result from attempt data."""
        question_summaries = self._create_question_summaries(attempts)
        metrics = self._calculate_metrics(question_summaries, len(attempts))

        return AssessmentResult(
            assessment_id=str(self._assessment_id),
            user_id=self._user.id,
            learning_objective_id=self._learning_objective.id,
            total_questions=metrics["total_questions"],
            attempted_questions=metrics["attempted_count"],
            correct_questions=metrics["correct_count"],
            incorrect_questions=metrics["incorrect_count"],
            unattempted_questions=metrics["unattempted_count"],
            overall_score=metrics["overall_score"],
            passing_threshold=self._config.passing_threshold,
            passed=metrics["passed"],
            completion_percentage=metrics["completion_percentage"],
            graded_at=datetime.now(timezone.utc),
            question_summaries=question_summaries,
        )

    @staticmethod
    def _create_question_summaries(
        attempts: List[StudentQuestionAttempt],
    ) -> List[QuestionAttemptSummary]:
        """Create question summaries from attempt data."""
        summaries = []

        for attempt in attempts:
            if attempt and attempt.total_attempts > 0:
                attempted = True
                is_correct = attempt.mastered
                score = attempt.best_score
            else:
                attempted = False
                is_correct = False
                score = 0.0

            summary = QuestionAttemptSummary(
                question_id=attempt.question_id,
                attempted=attempted,
                is_correct=is_correct,
                score=score,
                total_attempts=attempt.total_attempts if attempt else 0,
                mastered=attempt.mastered if attempt else False,
                best_score=attempt.best_score if attempt else 0.0,
                latest_score=attempt.latest_score if attempt else 0.0,
            )
            summaries.append(summary)

        return summaries

    def _calculate_metrics(
        self, summaries: List[QuestionAttemptSummary], total_questions: int
    ) -> dict:
        """Calculate assessment metrics from question summaries."""
        attempted_count = sum(1 for s in summaries if s.attempted)
        correct_count = sum(1 for s in summaries if s.is_correct)
        incorrect_count = attempted_count - correct_count
        unattempted_count = total_questions - attempted_count

        overall_score = correct_count / total_questions if total_questions > 0 else 0.0
        completion_percentage = (
            attempted_count / total_questions if total_questions > 0 else 0.0
        )
        passed = overall_score >= self._config.passing_threshold

        return {
            "total_questions": total_questions,
            "attempted_count": attempted_count,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unattempted_count": unattempted_count,
            "overall_score": overall_score,
            "completion_percentage": completion_percentage,
            "passed": passed,
        }
