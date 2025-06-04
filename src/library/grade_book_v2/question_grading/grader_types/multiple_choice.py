import logging

from src.library.grade_book_v2.question_grading.grader_types.base import (
    AbstractQuestionGrader,
)
from src.repository.graded_responses.data_types import StudentAnswer
from src.repository.question_repository.data_types import Question

logger = logging.getLogger(__name__)


class MultipleChoiceGrader(AbstractQuestionGrader):
    """
    Grader for multiple-choice questions.

    This grader compares the selected option IDs in an attempted answer
    with the correct option IDs from the question to determine correctness.
    """

    def grade(self, question: Question, attempted_answer: StudentAnswer) -> bool:
        """
        Grade a multiple-choice question by comparing selected options to correct options.

        Args:
            question (Question): The multiple-choice question to grade
            attempted_answer (AttemptedAnswer): The user's attempted answer

        Returns:
            bool: True if all and only correct options were selected, False otherwise
        """
        logger.debug(f"Grading multiple-choice question {question.id}")

        # Get correct options
        correct_options = [
            option.id for option in question.content.options if option.is_correct
        ]

        selected_options = attempted_answer.question_metadata["selected_option_ids"]

        logger.debug(f"Correct options: {correct_options}")
        logger.debug(f"Selected options: {selected_options}")

        is_correct = set(selected_options) == set(correct_options)
        logger.debug(f"Answer is {'correct' if is_correct else 'incorrect'}")

        return is_correct

    def calculate_score(self, is_correct: bool) -> float:
        """
        Calculate score for the question.

        Args:
            is_correct (bool): Whether the answer was correct

        Returns:
            float: 1.0 for correct answers, 0.0 for incorrect answers
        """
        score = 1.0 if is_correct else 0.0
        logger.debug(f"Calculated score: {score}")
        return score

    def __repr__(self):
        return f"<{type(self).__name__}()>"
