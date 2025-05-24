import logging
from abc import ABC, abstractmethod

from src.repository.question_repository.qn_repository_data_types import Question

from .data_types import AttemptedAnswer

logger = logging.getLogger(__name__)


class AbstractQuestionGrader(ABC):
    @abstractmethod
    def grade(self, question: Question, attempted_answer: AttemptedAnswer) -> bool:
        """Grade the question based on the attempted answer"""
        pass

    @abstractmethod
    def calculate_score(self, is_correct: bool) -> float:
        """Calculate the score based on correctness"""
        pass


class MultipleChoiceGrader(AbstractQuestionGrader):
    """
    Grader for multiple-choice questions.

    This grader compares the selected option IDs in an attempted answer
    with the correct option IDs from the question to determine correctness.
    """

    def grade(self, question: Question, attempted_answer: AttemptedAnswer) -> bool:
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
