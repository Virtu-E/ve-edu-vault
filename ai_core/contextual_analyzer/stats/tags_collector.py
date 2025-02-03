from typing import List, Protocol

from data_types.ai_core import QuestionAIContext


class IFailedTagsCollector(Protocol):
    def collect_failed_tags(self, questions: List[QuestionAIContext]) -> List[str]: ...


class FailedTagsCollector:
    def collect_failed_tags(self, questions: List[QuestionAIContext]) -> List[str]:
        """
        Collects and returns a list of unique tags from questions where attempts were not successful.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects containing question data.

        Returns:
            List[str]: A list of unique tags associated with failed question attempts.
        """
        failed_tags = []
        for question in questions:
            if not question.attempts.success:
                failed_tags.extend(question.tags)
        return list(set(failed_tags))
