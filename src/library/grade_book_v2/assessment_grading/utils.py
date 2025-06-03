from typing import List

from src.repository.question_repository.data_types import Question
from src.repository.student_attempts.data_types import StudentQuestionAttempt


class UnattemptedQuestionFinder:
    """Finds questions not yet attempted by a student."""

    def find_unattempted(
        self, questions: List[Question], student_attempts: List[StudentQuestionAttempt]
    ) -> List[Question]:
        """Get questions that haven't been attempted."""
        return self._get_unattempted_questions(questions, student_attempts)

    @staticmethod
    def _get_unattempted_questions(
        questions: List[Question], student_attempts: List[StudentQuestionAttempt]
    ) -> List[Question]:
        """Return questions with no attempts."""

        if not student_attempts:
            return questions

        if not questions:
            return []

        attempted_question_ids = {attempt.question_id for attempt in student_attempts}
        return [
            question
            for question in questions
            if question.id not in attempted_question_ids
        ]
