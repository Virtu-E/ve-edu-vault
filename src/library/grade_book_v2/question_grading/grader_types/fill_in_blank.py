import logging
from typing import List

from src.library.grade_book_v2.question_grading.grader_types.base import (
    AbstractQuestionGrader,
)
from src.repository.graded_responses.data_types import StudentAnswer
from src.repository.question_repository.data_types import Question

logger = logging.getLogger(__name__)


class FillInTheBlankGrader(AbstractQuestionGrader):
    """
    Grader for fill-in-the-blank questions.

    This grader compares the student's answers for each blank with the accepted
    answers from the question, considering case sensitivity and matching rules.
    """

    def grade(self, question: Question, attempted_answer: StudentAnswer) -> bool:
        """
        Grade a fill-in-the-blank question by comparing each blank answer to accepted answers.

        Args:
            question (Question): The fill-in-the-blank question to grade
            attempted_answer (StudentAnswer): The user's attempted answer

        Returns:
            bool: True if all blanks are answered correctly, False otherwise
        """
        logger.debug(f"Grading fill-in-the-blank question {question.id}")

        blank_answers = attempted_answer.question_metadata.get("blank_answers", {})
        blanks_config = question.content.blanks or []

        logger.debug(f"Student blank answers: {blank_answers}")
        logger.debug(f"Number of blanks to check: {len(blanks_config)}")

        all_correct = True
        correct_count = 0
        total_blanks = len(blanks_config)

        for blank in blanks_config:
            blank_id = str(blank.id)
            student_answer = blank_answers.get(blank_id, "").strip()

            is_blank_correct = self._grade_single_blank(
                student_answer,
                blank.accepted_answers,
                blank.case_sensitive,
                blank.exact_match,
            )

            if is_blank_correct:
                correct_count += 1
            else:
                all_correct = False

            logger.debug(
                f"Blank {blank_id}: '{student_answer}' -> {'correct' if is_blank_correct else 'incorrect'}"
            )

        logger.debug(f"Overall result: {correct_count}/{total_blanks} blanks correct")
        logger.debug(
            f"Answer is {'fully correct' if all_correct else 'not fully correct'}"
        )

        return all_correct

    @staticmethod
    def _grade_single_blank(
        student_answer: str,
        accepted_answers: List[str],
        case_sensitive: bool = False,
        exact_match: bool = True,
    ) -> bool:
        """
        Grade a single blank against accepted answers.

        Args:
            student_answer (str): The student's answer for this blank
            accepted_answers (List[str]): List of acceptable answers
            case_sensitive (bool): Whether comparison should be case sensitive
            exact_match (bool): Whether match must be exact or allow partial matching

        Returns:
            bool: True if the student answer matches any accepted answer
        """
        if not student_answer:
            return False

        # Normalize student answer
        normalized_student = student_answer.strip()
        if not case_sensitive:
            normalized_student = normalized_student.lower()

        for accepted in accepted_answers:
            normalized_accepted = accepted.strip()
            if not case_sensitive:
                normalized_accepted = normalized_accepted.lower()

            if exact_match:
                if normalized_student == normalized_accepted:
                    return True
            else:
                # For non-exact match, check if student answer contains the accepted answer
                # or if accepted answer contains the student answer
                if (
                    normalized_student in normalized_accepted
                    or normalized_accepted in normalized_student
                ):
                    return True

        return False

    def calculate_score(self, is_correct: bool) -> float:
        """
        Calculate score for the question.

        Args:
            is_correct (bool): Whether all blanks were answered correctly

        Returns:
            float: 1.0 for fully correct answers, 0.0 for incorrect answers
        """
        score = 1.0 if is_correct else 0.0
        logger.debug(f"Calculated score: {score}")
        return score
