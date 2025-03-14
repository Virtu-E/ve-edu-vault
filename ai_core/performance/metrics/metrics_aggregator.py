"""
ai_core.performance.metrics_aggregator
~~~~~~~~~~~~~~

This module contains code that is  responsible for aggregating the
users stats on a topic depending on the required correct questions
"""

import logging
from typing import Dict, List, TypeAlias

import pandas as pd

from ai_core.performance.data_types import DifficultyEnum, PerformanceStatsData
from ai_core.performance.metrics.metric_types import BaseMetric
from course_ware.data_types import QuestionMetadata

log = logging.getLogger(__name__)

SubTopicQuestionData: TypeAlias = Dict[str, QuestionMetadata]


class MetricsCalculator:
    """Base implementation of the metrics aggregator."""

    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the calculator.

        Args:
            required_correct_questions: Number of correct questions required
            to mark a difficulty as completed.
        """
        self._args = args
        self._kwargs = kwargs
        self._metrics = []

    def register_metrics(self, metrics: List[BaseMetric]) -> None:
        """
        Registers metrics that need to be aggregated.

        Args:
            metrics: List of BaseMetric subclasses to register

        Raises:
            ValueError: If any metric is not a subclass of BaseMetric or not registered with PerformanceStatsData
        """
        log.info(f"Registering {len(metrics)} metrics")

        invalid_metrics = [
            metric.name for metric in metrics if not isinstance(metric, BaseMetric)
        ]
        if invalid_metrics:
            error_msg = f"The following metrics must be subclasses of BaseMetric: {', '.join(invalid_metrics)}"
            log.error(error_msg)
            raise ValueError(error_msg)

        unregistered_metrics = [
            metric.name
            for metric in metrics
            if not hasattr(PerformanceStatsData, metric.name)
        ]
        if unregistered_metrics:
            error_msg = f"The following metrics are not registered with the performance stats dataclass: {', '.join(unregistered_metrics)}"
            log.error(error_msg)
            raise ValueError(error_msg)

        for metric in metrics:
            log.debug(f"Registered metric: {metric.name}")

        self._metrics = metrics
        log.info("All metrics successfully registered")

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
            log.error("No questions data to calculate metrics for.")
            raise ValueError("No questions data to calculate metrics for")

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

            metric_dict = dict()

            for metric in self._metrics:
                data = metric(difficulty_groups, self._args, self._kwargs)
                metric_dict[metric.name] = data

            return PerformanceStatsData(**metric_dict)

        except Exception as e:
            log.error("Error calculating performance stats: %s", str(e))
            raise e

    def __repr__(self) -> str:
        """Return a dev-friendly string representation."""
        return f"{type(self).__name__}({self._args}, {self._kwargs})"

    def __str__(self) -> str:
        """Return a user-friendly string representation."""
        return f"Metrics Calculator ( {self._args} {self._kwargs})"
