"""
ai_core.performance.metrics.metric_types
~~~~~~~~~~~~~~~~~~~

Holds the different metric types to be calculated
by the metrics aggregator. Can add metrics in this module
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, TypeAlias

import pandas as pd

from ai_core.performance.data_types import (CompletionStatusEnum,
                                            DifficultyCompletion,
                                            DifficultyEnum, DifficultyScore,
                                            RankedDifficulty)
from course_ware.data_types import QuestionMetadata

SubTopicQuestionData: TypeAlias = Dict[str, QuestionMetadata]

# NOTE : when adding New metrics, make sure to also add the data here
# : ai_core.performance.data_types.PerformanceStatsData


class BaseMetric(ABC):
    """Abstract interface for all metrics."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name of the metric."""
        raise NotImplementedError()

    def __call__(
        self, difficulty_groups: pd.core.groupby.GroupBy, *args, **kwargs
    ) -> Any:
        """Calculate metric from user question data.

        Args :
            difficulty_groups (pd.core.groupby.GroupBy): User question data in a pandas
            data frame Grouped by difficulty.

        Returns:
            objects (Any): The return type depends on the implementation detail.
        """
        raise NotImplementedError


class DifficultyScoreMetric(BaseMetric):
    """Calculates the users difficulty score on a particular topic given the user question data."""

    @property
    def name(self) -> str:
        """Returns the name of the metric."""
        return "difficulty_scores"

    def __call__(
        self, difficulty_groups: pd.core.groupby.GroupBy, *args, **kwargs
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


class DifficultyCompletionMetric(BaseMetric):
    """Calculates the completion status for each difficulty level."""

    @property
    def name(self) -> str:
        """Returns the name of the metric."""
        return "difficulty_completion"

    def __call__(
        self, difficulty_groups: pd.core.groupby.GroupBy, *args, **kwargs
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
            required_correct_questions = kwargs.get("required_correct_questions", False)
            if not required_correct_questions:
                raise ValueError(
                    "Please include 'required_correct_questions' argument in order to calculate completion status metric."
                )
            is_completed = correct_questions >= required_correct_questions
            difficulty_completion[DifficultyEnum(difficulty)] = (
                CompletionStatusEnum.COMPLETED
                if is_completed
                else CompletionStatusEnum.INCOMPLETE
            )

        return difficulty_completion


class DifficultyRankingMetric(BaseMetric):
    """Calculates and orders difficulties base on average question attempts."""

    @property
    def name(self) -> str:
        """Returns the name of the metric."""
        return "ranked_difficulties"

    def __call__(
        self, difficulty_groups: pd.core.groupby.GroupBy, *args, **kwargs
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
