import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Literal, TypeVar

import pandas as pd

from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata

log = logging.getLogger(__name__)

# Type definitions
DifficultyLiteral = Literal["easy", "medium", "hard"]
StatusLiteral = Literal["incomplete", "completed"]
T = TypeVar("T")


class PerformanceCalculatorInterface(ABC):
    """Abstract interface for performance calculators."""

    @abstractmethod
    def calculate_performance(
        self, question_data: Dict[str, QuestionMetadata]
    ) -> PerformanceStats:
        """Calculate performance statistics from question data."""
        raise NotImplementedError


class BasePerformanceCalculator(PerformanceCalculatorInterface):
    """Base implementation of the performance calculator."""

    def __init__(self, required_correct_questions: int = 0):
        """
        Initialize the calculator.

        Args:
            required_correct_questions: Number of correct questions required to mark a difficulty as completed.
        """
        self.required_correct_questions: int = required_correct_questions
        self.difficulties: List[DifficultyLiteral] = ["easy", "medium", "hard"]
        self.status_values: Dict[bool, StatusLiteral] = {
            True: "completed",
            False: "incomplete",
        }

    def validate_difficulty(self, difficulty: str) -> None:
        """
        Validate that a difficulty value is allowed.

        Args:
            difficulty: The difficulty value to validate.

        Raises:
            ValueError: If the difficulty is not one of the allowed values.
        """
        if difficulty not in self.difficulties:
            raise ValueError(
                f"Invalid difficulty: {difficulty}. Must be one of {self.difficulties}"
            )

    def calculate_performance(
        self, question_data: Dict[str, QuestionMetadata]
    ) -> PerformanceStats:
        """
        Calculate performance statistics from question data.

        Args:
            question_data: Dictionary mapping question IDs to their metadata.

        Returns:
            PerformanceStats object containing the calculated statistics.
        """
        if not question_data:
            return self._create_empty_stats()

        try:
            # Convert question data to DataFrame for analysis
            df = pd.DataFrame([data.model_dump() for data in question_data.values()])

            for difficulty in df["difficulty"].unique():
                self.validate_difficulty(difficulty)

            difficulty_groups = df.groupby("difficulty")

            difficulty_status = self._calculate_difficulty_status(difficulty_groups)
            ranked_difficulties = self._rank_difficulties(difficulty_groups)
            difficulty_scores = self._calculate_difficulty_scores(difficulty_groups)

            return PerformanceStats(
                ranked_difficulties=ranked_difficulties,
                difficulty_status=difficulty_status,
                difficulty_scores=difficulty_scores,  # New field added to PerformanceStats
            )

        except Exception as e:
            log.error(f"Error calculating performance stats: {str(e)}")
            raise e

    def _calculate_difficulty_scores(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> Dict[DifficultyLiteral, int]:
        """
        Calculate the number of correct answers for each difficulty level.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            Dictionary mapping difficulties to their scores (number of correct answers).
        """
        difficulty_scores: Dict[DifficultyLiteral, int] = {
            diff: 0 for diff in self.difficulties
        }

        for difficulty in self.difficulties:
            group = (
                difficulty_groups.get_group(difficulty)
                if difficulty in difficulty_groups.groups
                else pd.DataFrame()
            )
            if not group.empty:
                difficulty_scores[difficulty] = int(group["is_correct"].sum())

        return difficulty_scores

    def _calculate_difficulty_status(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> Dict[DifficultyLiteral, StatusLiteral]:
        """
        Calculate completion status for each difficulty level.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            Dictionary mapping difficulties to their completion status.
        """
        difficulty_status: Dict[DifficultyLiteral, StatusLiteral] = {
            diff: self.status_values[False] for diff in self.difficulties
        }

        for difficulty, group in difficulty_groups:
            self.validate_difficulty(difficulty)
            correct_questions = len(group[group["is_correct"]])
            is_completed = correct_questions >= self.required_correct_questions
            difficulty_status[difficulty] = self.status_values[is_completed]

        return difficulty_status

    def _rank_difficulties(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> List[tuple[DifficultyLiteral, float]]:
        """
        Rank difficulties based on average attempts.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            List of tuples containing difficulty and average attempts, sorted by attempts.
        """
        avg_attempts: Dict[DifficultyLiteral, float] = {}

        # Calculate average attempts for all difficulties
        for difficulty in self.difficulties:
            self.validate_difficulty(difficulty)
            group = (
                difficulty_groups.get_group(difficulty)
                if difficulty in difficulty_groups.groups
                else pd.DataFrame()
            )
            avg_attempts[difficulty] = (
                group["attempt_number"].mean() if not group.empty else 0.0
            )

        # Sort by average attempts in ascending order
        return sorted(avg_attempts.items(), key=lambda x: x[1])

    def _create_empty_stats(self) -> PerformanceStats:
        """
        Create empty performance stats.

        Returns:
            PerformanceStats object with default values.
        """
        return PerformanceStats(
            ranked_difficulties=[(diff, 0.0) for diff in self.difficulties],
            difficulty_status={
                diff: self.status_values[False] for diff in self.difficulties
            },
            difficulty_scores={
                diff: 0 for diff in self.difficulties
            },  # Added new field
        )
