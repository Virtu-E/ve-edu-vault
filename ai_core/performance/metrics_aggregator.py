"""
ai_core.performance.metrics_aggregator
~~~~~~~~~~~~~~

This module contains code that is  responsible for aggregating the
users stats on a topic depending on the required correct questions
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, TypeAlias

import pandas as pd

from course_ware.data_types import QuestionMetadata

from ..learning_mode_rules import LearningModeType
from .data_types import (
    CompletionStatusEnum,
    DifficultyCompletion,
    DifficultyEnum,
    DifficultyScore,
    PerformanceStatsData,
    RankedDifficulty,
)

log = logging.getLogger(__name__)

SubTopicQuestionData: TypeAlias = Dict[str, QuestionMetadata]


class MetricsAggregatorBase(ABC):
    """Abstract interface for metrics aggregator."""

    @abstractmethod
    def aggregate_metrics(
        self, question_data: SubTopicQuestionData
    ) -> PerformanceStatsData:
        """Calculate performance statistics from question data."""
        raise NotImplementedError


class MetricsCalculator(MetricsAggregatorBase):
    """Base implementation of the metrics aggregator."""

    __slots__ = ("_required_correct_questions",)

    def __init__(self, required_correct_questions: int = 0):
        """
        Initialize the calculator.

        Args:
            required_correct_questions: Number of correct questions required
            to mark a difficulty as completed.
        """
        self._required_correct_questions: int = required_correct_questions

    def aggregate_metrics(
        self, question_data: SubTopicQuestionData
    ) -> PerformanceStatsData:
        """
        Aggregate question metric data from sub_topic question data.

        Args:
            question_data: Dictionary mapping question IDs to their
            sub_topic question metadata.

        Returns:
            PerformanceStats object containing the calculated statistics.
        """
        if not question_data:
            log.info(
                "No questions data to calculate metrics for. Returning empty data."
            )
            return self._create_empty_stats()

        try:
            # Convert question data to DataFrame for analysis
            df = pd.DataFrame([data.model_dump() for data in question_data.values()])

            for difficulty in df["difficulty"].unique():
                try:
                    DifficultyEnum(difficulty)
                except ValueError:
                    valid_options = [e.value for e in DifficultyEnum]
                    raise ValueError(
                        "Invalid difficulty: %s. Must be one of %s",
                        difficulty,
                        valid_options,
                    )

            # Group the dataframe by difficulty level
            difficulty_groups = df.groupby("difficulty")

            # The difficulty_groups object contains:
            #
            # 1. Keys: difficulty levels as strings ("easy", "medium", "hard")
            #
            # 2. Values: DataFrames for each difficulty group with structure:
            #    question_id | attempt_number | is_correct | sub_topic       | difficulty
            #    -----------|----------------|------------|-------------|------------
            #    q123abc    | 1              | True       | addition | easy
            #    q456def    | 2              | True       | division | easy
            #    q789ghi    | 1              | False      | multiplication    | easy
            #
            # When iterating with "for difficulty, group in difficulty_groups:",
            # 'difficulty' will be the string key and 'group' will be the DataFrame

            difficulty_status = self._calculate_difficulty_completion(difficulty_groups)
            ranked_difficulties = self._rank_difficulties(difficulty_groups)
            difficulty_scores = self._calculate_difficulty_scores(difficulty_groups)

            return PerformanceStatsData(
                ranked_difficulties=ranked_difficulties,
                difficulty_completion=difficulty_status,
                difficulty_scores=difficulty_scores,
            )

        except Exception as e:
            log.error("Error calculating performance stats: %s", str(e))
            raise e

    @staticmethod
    def _calculate_difficulty_scores(
        difficulty_groups: pd.core.groupby.GroupBy,
    ) -> DifficultyScore:
        """
        Calculate the number of correct answers for each difficulty level.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            Dictionary mapping difficulties to their scores (number of correct answers).
        """
        difficulty_scores: DifficultyScore = defaultdict(lambda: 0)
        for difficulty in DifficultyEnum:
            group = (
                difficulty_groups.get_group(difficulty.value)
                if difficulty in difficulty_groups.groups
                else pd.DataFrame()
            )
            if not group.empty:
                difficulty_scores[difficulty] = int(group["is_correct"].sum())

        return difficulty_scores

    def _calculate_difficulty_completion(
        self, difficulty_groups: pd.core.groupby.GroupBy
    ) -> DifficultyCompletion:
        """
        Calculate completion status for each difficulty level.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            Dictionary mapping difficulties to their completion status.
        """
        difficulty_completion: DifficultyCompletion = {
            diff: CompletionStatusEnum.INCOMPLETE for diff in DifficultyEnum
        }

        for difficulty, group in difficulty_groups:
            correct_questions = len(group[group["is_correct"]])
            is_completed = correct_questions >= self._required_correct_questions
            difficulty_completion[DifficultyEnum(difficulty)] = (
                CompletionStatusEnum.COMPLETED
                if is_completed
                else CompletionStatusEnum.INCOMPLETE
            )

        return difficulty_completion

    @staticmethod
    def _rank_difficulties(
        difficulty_groups: pd.core.groupby.GroupBy,
    ) -> RankedDifficulty:
        """
        Rank difficulties based on average attempts.

        Args:
            difficulty_groups: Grouped DataFrame by difficulty.

        Returns:
            List of tuples containing difficulty and average attempts, sorted by attempts.
        """
        avg_attempts: Dict[DifficultyEnum, float] = defaultdict(lambda: 0.0)

        # Calculate average attempts for all difficulties
        for difficulty in DifficultyEnum:
            group = (
                difficulty_groups.get_group(difficulty.value)
                if difficulty in difficulty_groups.groups
                else pd.DataFrame()
            )
            avg_attempts[difficulty] = (
                group["attempt_number"].mean() if not group.empty else 0.0
            )

        # Sort by average attempts in ascending order
        return sorted(avg_attempts.items(), key=lambda x: x[1])

    @staticmethod
    def _create_empty_stats() -> PerformanceStatsData:
        """
        Create empty performance stats.

        Returns:
            PerformanceStats object with default values.
        """

        log.info("Creating empty performance stats.")

        return PerformanceStatsData(
            ranked_difficulties=[(diff, 0.0) for diff in DifficultyEnum],
            difficulty_completion={
                diff: CompletionStatusEnum.INCOMPLETE for diff in DifficultyEnum
            },
            difficulty_scores={diff: 0 for diff in DifficultyEnum},
        )

    @classmethod
    def get_metric_calculator(
        cls, learning_mode: LearningModeType
    ) -> "MetricsCalculator":
        # TODO : finish implementation of this
        """
        Factory method for creating metric calculators.

        Args:
            learning_mode: (LearningModeType) --> the users current learning mode.
        """
        return cls(0)

    def __repr__(self) -> str:
        """Return a dev-friendly string representation."""
        return f"{type(self).__name__}({self._required_correct_questions})"

    def __str__(self) -> str:
        """Return a user-friendly string representation."""
        return (
            f"Metrics Calculator (requires {self._required_correct_questions} "
            f"correct questions to complete a difficulty)"
        )
