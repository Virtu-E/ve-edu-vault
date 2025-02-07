from typing import Dict, List, Protocol

from data_types.ai_core import QuestionAIContext


class ICompletionAnalyzer(Protocol):
    def analyze_completion(
        self, questions: List[QuestionAIContext]
    ) -> Dict[str, float]: ...


class CompletionAnalyzer:
    MAX_ATTEMPTS = 3

    def analyze_completion(
        self, questions: List[QuestionAIContext]
    ) -> Dict[str, float]:
        """
        Analyze completion statistics for a list of questions based on their attempts.

        Args:
            questions (List[QuestionAIContext]): A list of `QuestionAIContext` objects containing
                data about questions, their attempts, and outcomes.

        Returns:
            Dict[str, float]: A dictionary with the following metrics:
                - "completionRate" (float): Percentage of successfully completed questions.
                - "incompleteRate" (float): Percentage of questions that were not successfully completed
                  after reaching the maximum number of attempts.
                - "earlyAbandonment" (float): Percentage of questions abandoned before reaching
                  the maximum number of allowed attempts.
        """

        if not questions:
            return {
                "completionRate": 0.0,
                "incompleteRate": 0.0,
                "earlyAbandonment": 0.0,
            }

        total = len(questions)
        completed = sum(1 for q in questions if q.attempts.success)
        max_attempts_failed = sum(
            1
            for q in questions
            if not q.attempts.success and q.attempts.attemptNumber == self.MAX_ATTEMPTS
        )
        early_abandoned = sum(
            1
            for q in questions
            if not q.attempts.success and q.attempts.attemptNumber < self.MAX_ATTEMPTS
        )

        return {
            "completionRate": round((completed / total) * 100, 1),
            "incompleteRate": round((max_attempts_failed / total) * 100, 1),
            "earlyAbandonment": round((early_abandoned / total) * 100, 1),
        }
