from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal, Union

import pandas as pd

from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata


class DifficultyStatus(Enum):
    """Enum for difficulty completion status."""

    COMPLETED = "completed"
    INCOMPLETE = "incomplete"


class PerformanceCalculatorInterface(ABC):
    @abstractmethod
    def calculate_performance(
        self, question_data: dict[str, QuestionMetadata]
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
    # TODO : need to extract this to an .env file at some point
    COMPLETION_THRESHOLD = 2 / 3  # Class constant for completion threshold

    def calculate_performance(
        self, question_data: dict[str, QuestionMetadata]
    ) -> PerformanceStats:
        """
        Calculate performance based on question attempts and difficulty levels of a particular topic.

        Args:
            question_data: Dictionary containing question metadata

        Returns:
            PerformanceStats: Contains ranked difficulties and their completion status
        """
        if not question_data:
            return PerformanceStats(ranked_difficulties=[], difficulty_status={})
        # dumping the data to JSON due to the way pandas work. If Pydantic model is sent,
        # it won't be able to see all the available data fields
        df = pd.DataFrame([data.model_dump() for data in question_data.values()])
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

        return PerformanceStats(
            ranked_difficulties=ranked_difficulties, difficulty_status=difficulty_status
        )

    def _calculate_difficulty_status(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> Union[
        dict[Literal["easy", "medium", "hard"], Literal["incomplete", "completed"]], {}
    ]:
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
            completed_questions = group["is_correct"].value_counts().get(True, 0)

            status = (
                DifficultyStatus.COMPLETED
                if completed_questions >= self.COMPLETION_THRESHOLD * total_questions
                else DifficultyStatus.INCOMPLETE
            )
            difficulty_status[difficulty] = status.value

        return difficulty_status

    @staticmethod
    def _rank_incomplete_difficulties(
        difficulty_groups: pd.core.groupby.GroupBy,
        incomplete_difficulties: list[str],
    ) -> list[tuple[Literal["hard", "medium", "easy"], float]]:
        """
        Rank incomplete difficulties based on average attempts.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty
            incomplete_difficulties: List of difficulties marked as incomplete

        Returns:
            List of tuples containing difficulty and average attempts, sorted by attempts
            in descending order. Returns an empty list if no matching difficulties are found.
        """
        avg_attempts = {
            difficulty: group["attempt_number"].mean()
            for difficulty, group in difficulty_groups
            if difficulty in incomplete_difficulties
        }

        return sorted(avg_attempts.items(), key=lambda x: x[1], reverse=True)
