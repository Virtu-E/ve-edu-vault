from typing import Protocol, List

from data_types.ai_core import QuestionAIContext


class IQuestionFilter(Protocol):
    def filter_by_difficulty(self, questions: List[QuestionAIContext], difficulty: str) -> List[QuestionAIContext]: ...


class QuestionFilter(IQuestionFilter):
    def filter_by_difficulty(self, questions: List[QuestionAIContext], difficulty: str) -> List[QuestionAIContext]:
        return [q for q in questions if q.difficulty == difficulty]
