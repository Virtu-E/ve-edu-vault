from abc import ABC, abstractmethod
from typing import List, Dict

from data_types.ai_core import QuestionAIContext, Attempt
from exceptions import InvalidQuestionConfiguration
from repository.shared import QuestionRepository


class QuestionContextBuilderInterface(ABC):
    """Interface for building question contexts"""

    @abstractmethod
    def build_question_context(self, question_ids: List[str], question_metadata: Dict) -> List[QuestionAIContext]:
        """Build question contexts for AI analysis"""
        pass


class QuestionContextBuilder(QuestionContextBuilderInterface):
    """Builds question context for AI analysis"""

    def __init__(self, question_repository: QuestionRepository):
        self.question_repository = question_repository

    def build_question_context(self, question_ids: List[str], question_metadata: Dict) -> List[QuestionAIContext]:
        """
        Build question contexts for AI analysis.

        Args:
            question_ids (List[str]): List of question IDs to retrieve and process.
            question_metadata (Dict): Dictionary containing metadata for each question.

        Returns:
            List[QuestionAIContext]: A list of question contexts containing AI-ready data.
        """
        questions = self.question_repository.get_questions_by_ids(question_ids)
        question_contexts = []

        for question in questions:
            attempt_data = question_metadata.get(question.id)
            if not attempt_data:
                raise InvalidQuestionConfiguration(f"Question {question.id} not found in attempt data")

            attempt = Attempt(success=attempt_data.is_correct, timeSpent=90, attemptNumber=attempt_data.attempt_number)

            context = QuestionAIContext(_id=question.id, difficulty=question.difficulty, tags=question.tags, attempts=attempt)

            question_contexts.append(context)

        return question_contexts
