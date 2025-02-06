from typing import Dict, List, Protocol

from data_types.ai_core import QuestionAIContext


class IAttemptStatsCalculator(Protocol):
    def calculate_total_attempts(self, questions: List[QuestionAIContext]) -> int: ...
    def calculate_success_rate(self, questions: List[QuestionAIContext]) -> float: ...
    def calculate_attempt_specific_rates(self, questions: List[QuestionAIContext]) -> Dict[str, float]: ...


class AttemptStatsCalculator:
    MAX_ATTEMPTS = 3

    @staticmethod
    def calculate_total_attempts(questions: List[QuestionAIContext]) -> int:
        """
        Calculate the total number of attempts made for all given questions.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects.

        Returns:
            int: The total number of attempts made across all questions.
        """
        return sum(q.attempts.attemptNumber for q in questions)

    @staticmethod
    def calculate_success_rate(questions: List[QuestionAIContext]) -> float:
        """
        Calculates the success rate across all given questions as a percentage.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects.

        Returns:
            float: The success rate as a percentage.
        """
        if not questions:
            return 0.0 * 100
        successful = sum(1 for q in questions if q.attempts.success)
        return round((successful / len(questions)) * 100, 1)

    @staticmethod
    def calculate_attempt_specific_rates(
        questions: List[QuestionAIContext],
    ) -> Dict[str, float]:
        """
        Calculates the success rates for each attempt (first, second, and third)
                across all the given questions as a percentage.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects.

        Returns:
            Dict[str, float]: A dictionary containing success rates for each attempt level.
                            The keys are "first", "second", and "third", and their
                            corresponding values are the success rates as percentages.
        """
        if not questions:
            return {"first": 0.0, "second": 0.0, "third": 0.0}

        total = len(questions)
        rates = {
            "first": round(
                (sum(1 for q in questions if q.attempts.success and q.attempts.attemptNumber == 1) / total) * 100,
                1,
            ),
            "second": round(
                (sum(1 for q in questions if q.attempts.success and q.attempts.attemptNumber == 2) / total) * 100,
                1,
            ),
            "third": round(
                (sum(1 for q in questions if q.attempts.success and q.attempts.attemptNumber == 3) / total) * 100,
                1,
            ),
        }
        return rates
