import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Literal

import pandas as pd

from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata

log = logging.getLogger(__name__)


class LearningMode(Enum):
    NORMAL = "normal"
    RECOVERY = "recovery"
    REINFORCEMENT = "reinforcement"


class PerformanceCalculatorInterface(ABC):
    @abstractmethod
    def calculate_performance(self, question_data: Dict[str, QuestionMetadata]) -> PerformanceStats:
        raise NotImplementedError


class BasePerformanceCalculator(PerformanceCalculatorInterface):
    def __init__(self):
        self.required_correct_questions = 0
        self.difficulties = ["easy", "medium", "hard"]

    def calculate_performance(self, question_data: Dict[str, QuestionMetadata]) -> PerformanceStats:
        if not question_data:
            return self._create_empty_stats()

        df = pd.DataFrame([data.model_dump() for data in question_data.values()])
        difficulty_groups = df.groupby("difficulty")

        difficulty_status = self._calculate_difficulty_status(difficulty_groups)
        ranked_difficulties = self._rank_difficulties(difficulty_groups)

        return PerformanceStats(ranked_difficulties=ranked_difficulties, difficulty_status=difficulty_status)

    def _calculate_difficulty_status(self, difficulty_groups: pd.core.groupby.GroupBy) -> Dict[Literal["easy", "medium", "hard"], Literal["incomplete", "completed"]]:
        difficulty_status = {}

        # Initialize all difficulties as incomplete
        for diff in self.difficulties:
            difficulty_status[diff] = "incomplete"

        for difficulty, group in difficulty_groups:
            correct_questions = len(group[group["is_correct"] == True])
            if correct_questions >= self.required_correct_questions:
                difficulty_status[difficulty] = "completed"

        return difficulty_status

    def _rank_difficulties(self, difficulty_groups: pd.core.groupby.GroupBy) -> List[tuple[Literal["easy", "medium", "hard"], float]]:
        avg_attempts = {}

        # Calculate average attempts for all difficulties
        for difficulty in self.difficulties:
            group = difficulty_groups.get_group(difficulty) if difficulty in difficulty_groups.groups else pd.DataFrame()
            avg_attempts[difficulty] = group["attempt_number"].mean() if not group.empty else 0.0

        # Sort by average attempts in ascending order
        return sorted(avg_attempts.items(), key=lambda x: x[1])

    def _create_empty_stats(self) -> PerformanceStats:
        return PerformanceStats(
            ranked_difficulties=[(diff, 0.0) for diff in self.difficulties],
            difficulty_status={diff: "incomplete" for diff in self.difficulties},
        )


class NormalModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 2  # Need 2 correct questions PER difficulty


class RecoveryModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 4  # Need 4 correct questions PER difficulty


class ReinforcementModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 3  # 3/3 questions need to be correct / all questions on the difficulty cleared


class PerformanceCalculatorFactory:
    @staticmethod
    def create_calculator(mode: LearningMode) -> PerformanceCalculatorInterface:
        calculators = {
            LearningMode.NORMAL: NormalModeCalculator,
            LearningMode.RECOVERY: RecoveryModeCalculator,
            LearningMode.REINFORCEMENT: ReinforcementModeCalculator,
        }

        calculator_class = calculators.get(mode)
        if not calculator_class:
            raise ValueError(f"Unsupported learning mode: {mode}")

        return calculator_class()
