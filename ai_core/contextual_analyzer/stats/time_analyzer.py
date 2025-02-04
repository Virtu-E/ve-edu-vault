from typing import List, Dict, Protocol

from data_types.ai_core import QuestionAIContext


class ITimeAnalyzer(Protocol):
    def analyze_time(self, questions: List[QuestionAIContext]) -> Dict[str, float]: ...


class TimeAnalyzer:
    def analyze_time(self, questions: List[QuestionAIContext]) -> Dict[str, float]:
        """
        Analyzes the time statistics for a list of questions.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects containing attempt data.

        Returns:
            Dict[str, float]: A dictionary containing average time statistics and time distribution data.
        """
        if not questions:
            return {
                "averageTime": 0.0,
                "averageFirstAttemptTime": 0.0,
                "averageSecondAttemptTime": 0.0,
                "averageThirdAttemptTime": 0.0,
                "timeDistribution": {
                    "firstAttempt": 0.0,
                    "secondAttempt": 0.0,
                    "thirdAttempt": 0.0,
                },
            }

        time_by_attempt = self._group_time_by_attempt(questions)
        averages = self._calculate_time_averages(time_by_attempt)
        distribution = self._calculate_time_distribution(time_by_attempt)

        return {**averages, "timeDistribution": distribution}

    def _group_time_by_attempt(self, questions: List[QuestionAIContext]) -> Dict[str, List[int]]:
        """
        Groups the time spent for each attempt type (first, second, third) across the given questions.

        Args:
            questions (List[QuestionAIContext]): A list of QuestionAIContext objects.

        Returns:
            Dict[str, List[int]]: A dictionary where keys are attempt types ("first", "second", "third")
                                  and values are lists of times spent on these attempts.
        """
        return {
            "first": [q.attempts.timeSpent for q in questions if q.attempts.attemptNumber >= 1],
            "second": [q.attempts.timeSpent for q in questions if q.attempts.attemptNumber >= 2],
            "third": [q.attempts.timeSpent for q in questions if q.attempts.attemptNumber == 3],
        }

    def _calculate_time_averages(self, time_by_attempt: Dict[str, List[int]]) -> Dict[str, float]:
        """
        Calculates the average time spent on each attempt type.

        Args:
            time_by_attempt (Dict[str, List[int]]): A dictionary of times grouped by attempt types.

        Returns:
            Dict[str, float]: A dictionary where keys are average time metrics (e.g., "averageFirstAttemptTime")
                              and values are the corresponding average times.
        """
        averages = {}
        for attempt, times in time_by_attempt.items():
            if times:
                averages[f"average{attempt.capitalize()}AttemptTime"] = sum(times) / len(times)
            else:
                averages[f"average{attempt.capitalize()}AttemptTime"] = 0.0
        return averages

    def _calculate_time_distribution(self, time_by_attempt: Dict[str, List[int]]) -> Dict[str, float]:
        """
        Calculates the distribution of time spent across different attempt types.

        Args:
            time_by_attempt (Dict[str, List[int]]): A dictionary of times grouped by attempt types.

        Returns:
            Dict[str, float]: A dictionary where keys are time distribution metrics (e.g., "firstAttempt")
                              and values are the percentage of total time spent on each attempt type.
        """
        total_time = sum(sum(times) for times in time_by_attempt.values())
        if total_time == 0:
            return {f"{k}Attempt": 0.0 for k in time_by_attempt.keys()}

        return {f"{k}Attempt": sum(times) / total_time for k, times in time_by_attempt.items()}
