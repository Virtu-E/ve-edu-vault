from abc import ABC, abstractmethod

from src.repository.graded_responses.data_types import StudentAnswer
from src.repository.question_repository.data_types import Question


class AbstractQuestionGrader(ABC):
    @abstractmethod
    def grade(self, question: Question, attempted_answer: StudentAnswer) -> bool:
        """Grade the question based on the attempted answer"""
        pass

    @abstractmethod
    def calculate_score(self, is_correct: bool) -> float:
        """Calculate the score based on correctness"""
        pass
