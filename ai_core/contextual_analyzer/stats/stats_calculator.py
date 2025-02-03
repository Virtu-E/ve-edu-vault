from abc import abstractmethod, ABC
from typing import List

from ai_core.contextual_analyzer.stats.attempts_calculator import AttemptStatsCalculator, IAttemptStatsCalculator
from ai_core.contextual_analyzer.stats.completion_analyzer import CompletionAnalyzer, ICompletionAnalyzer
from ai_core.contextual_analyzer.stats.question_filter import QuestionFilter, IQuestionFilter
from ai_core.contextual_analyzer.stats.tags_collector import FailedTagsCollector, IFailedTagsCollector
from ai_core.contextual_analyzer.stats.time_analyzer import TimeAnalyzer, ITimeAnalyzer
from data_types.ai_core import QuestionAIContext, DifficultyStats


class DifficultyStatsCalculatorInterface(ABC):
    @abstractmethod
    def calculate(self, questions: List[QuestionAIContext], difficulty: str) -> DifficultyStats:
        """
         Calculate comprehensive difficulty-based statistics for the given set of questions.

        Args:
            questions (List[QuestionAIContext]): A list of questions containing attempts and metadata.
            difficulty (str): The difficulty level to filter and calculate statistics for.

        Returns:
            DifficultyStats: An object containing detailed statistics including attempt-based stats,
            time-based stats, completion stats, and failed tags.

        """
        raise NotImplementedError


class DifficultyStatsCalculator(DifficultyStatsCalculatorInterface):
    """
    Calculates statistical data based on question attempts and difficulty levels using injected dependencies.
    """

    def __init__(self, question_filter: IQuestionFilter, attempt_calculator: IAttemptStatsCalculator, time_analyzer: ITimeAnalyzer, completion_analyzer: ICompletionAnalyzer, tags_collector: IFailedTagsCollector):
        """
        Initialize the calculator with the required dependencies.

        Args:
            question_filter (IQuestionFilter): Component to filter questions by difficulty.
            attempt_calculator (IAttemptStatsCalculator): Component to calculate attempt-based stats.
            time_analyzer (ITimeAnalyzer): Component to analyze time-based stats.
            completion_analyzer (ICompletionAnalyzer): Component to calculate completion stats.
            tags_collector (IFailedTagsCollector): Component to collect failed tags from questions.
        """
        self._question_filter = question_filter
        self._attempt_calculator = attempt_calculator
        self._time_analyzer = time_analyzer
        self._completion_analyzer = completion_analyzer
        self._tags_collector = tags_collector

    def calculate(self, questions: List[QuestionAIContext], difficulty: str) -> DifficultyStats:
        """
        Calculate comprehensive difficulty-based statistics for the given set of questions.

        Args:
            questions (List[QuestionAIContext]): A list of questions containing attempts and metadata.
            difficulty (str): The difficulty level to filter and calculate statistics for.

        Returns:
            DifficultyStats: An object containing detailed statistics including attempt-based stats,
                             time-based stats, completion stats, and failed tags.
        """
        filtered_questions = self._question_filter.filter_by_difficulty(questions, difficulty)

        if not filtered_questions:
            return self._empty_stats()

        total_attempts = self._attempt_calculator.calculate_total_attempts(filtered_questions)
        if total_attempts == 0:
            return self._empty_stats()

        success_rate = self._attempt_calculator.calculate_success_rate(filtered_questions)
        attempt_rates = self._attempt_calculator.calculate_attempt_specific_rates(filtered_questions)

        time_stats = self._time_analyzer.analyze_time(filtered_questions)

        completion_stats = self._completion_analyzer.analyze_completion(filtered_questions)

        failed_tags = self._tags_collector.collect_failed_tags(filtered_questions)

        successful_attempts = [q.attempts.attemptNumber for q in filtered_questions if q.attempts.success]
        avg_attempts_to_success = (sum(successful_attempts) / len(successful_attempts)) if successful_attempts else 0

        return DifficultyStats(
            totalAttempts=total_attempts,
            successRate=success_rate,
            averageTime=time_stats["averageFirstAttemptTime"],
            failedTags=failed_tags,
            firstAttemptSuccessRate=attempt_rates["first"],
            secondAttemptSuccessRate=attempt_rates["second"],
            thirdAttemptSuccessRate=attempt_rates["third"],
            averageAttemptsToSuccess=avg_attempts_to_success,
            completionRate=completion_stats["completionRate"],
            incompleteRate=completion_stats["incompleteRate"],
            earlyAbandonment=completion_stats["earlyAbandonment"],
            averageFirstAttemptTime=time_stats["averageFirstAttemptTime"],
            averageSecondAttemptTime=time_stats["averageSecondAttemptTime"],
            averageThirdAttemptTime=time_stats["averageThirdAttemptTime"],
            timeDistribution=time_stats,
        )

    def _empty_stats(self) -> DifficultyStats:
        """
        Generate empty statistics for cases where no data is available.

        Returns:
            DifficultyStats: An object representing empty values for all stats fields.
        """
        return DifficultyStats(totalAttempts=0, successRate=0.0, averageTime=0.0, failedTags=[], firstAttemptSuccessRate=0.0, secondAttemptSuccessRate=0.0, thirdAttemptSuccessRate=0.0, averageAttemptsToSuccess=0.0, completionRate=0.0, incompleteRate=0.0, earlyAbandonment=0.0, averageFirstAttemptTime=0.0, averageSecondAttemptTime=0.0, averageThirdAttemptTime=0.0, timeDistribution={"firstAttempt": 0.0, "secondAttempt": 0.0, "thirdAttempt": 0.0})


def create_difficulty_stats_calculator() -> DifficultyStatsCalculator:
    """
    Create and return an instance of DifficultyStatsCalculator with default dependencies.

    Returns:
        DifficultyStatsCalculator: An initialized instance of the calculator.
    """
    return DifficultyStatsCalculator(question_filter=QuestionFilter(), attempt_calculator=AttemptStatsCalculator(), time_analyzer=TimeAnalyzer(), completion_analyzer=CompletionAnalyzer(), tags_collector=FailedTagsCollector())
