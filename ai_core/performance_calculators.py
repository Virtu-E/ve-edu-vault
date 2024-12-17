from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import pandas as pd

from data_types.course_ware_schema import QuestionMetadata
from data_types.performance import PerformanceStats


class DifficultyStatus(Enum):
    """Enum for difficulty completion status."""

    COMPLETED = "completed"
    INCOMPLETE = "incomplete"


class PerformanceCalculatorInterface(ABC):
    @abstractmethod
    def calculate_performance(
        self, question_data: dict[str, QuestionMetadata | Any]
    ) -> PerformanceStats:
        """
        Abstract method to calculate user's performance on a topic.

        Args:
            question_data: Dictionary containing question metadata

        Returns:
            PerformanceStats: Calculated performance statistics
        """
        raise NotImplementedError


class AttemptBasedDifficultyRankerCalculator(PerformanceCalculatorInterface):
    COMPLETION_THRESHOLD = 2 / 3  # Class constant for completion threshold

    def calculate_performance(
        self, question_data: dict[str, QuestionMetadata | Any]
    ) -> PerformanceStats:
        """
        Calculate performance based on question attempts and difficulty levels.

        Args:
            question_data: Dictionary containing question metadata

        Returns:
            PerformanceStats: Contains ranked difficulties and their completion status
        """
        if not question_data:
            return PerformanceStats([], {})

        df = pd.DataFrame([data for data in question_data.values()])
        difficulty_groups = df.groupby("difficulty")

        difficulty_status = self._calculate_difficulty_status(difficulty_groups)
        incomplete_difficulties = [
            diff
            for diff, status in difficulty_status.items()
            if status == DifficultyStatus.INCOMPLETE.value
        ]

        ranked_difficulties = self._rank_incomplete_difficulties(
            difficulty_groups, incomplete_difficulties
        )

        return PerformanceStats(ranked_difficulties, difficulty_status)

    def _calculate_difficulty_status(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> dict[str, str]:
        """
        Calculate completion status for each difficulty level.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty

        Returns:
            Dict mapping difficulty levels to their completion status
        """
        difficulty_status = {}

        for difficulty, group in difficulty_groups:
            total_questions = len(group)
            completed_questions = (
                group["is_correct"].str.lower().value_counts().get("true", 0)
            )

            status = (
                DifficultyStatus.COMPLETED
                if completed_questions >= self.COMPLETION_THRESHOLD * total_questions
                else DifficultyStatus.INCOMPLETE
            )
            difficulty_status[difficulty] = status.value

        return difficulty_status

    def _rank_incomplete_difficulties(
        self,
        difficulty_groups: pd.core.groupby.GroupBy,
        incomplete_difficulties: list[str],
    ) -> list[tuple[str, float]]:
        """
        Rank incomplete difficulties based on average attempts.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty
            incomplete_difficulties: List of difficulties marked as incomplete

        Returns:
            List of tuples containing difficulty and average attempts, sorted
        """
        avg_attempts = {
            difficulty: group["attempt_number"].mean()
            for difficulty, group in difficulty_groups
            if difficulty in incomplete_difficulties
        }

        return sorted(avg_attempts.items(), key=lambda x: x[1], reverse=True)
