"""
Implementation of the Learning Mode system using the State Pattern
"""

from abc import ABC, abstractmethod
from fractions import Fraction
from typing import List, Literal

from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory
from ai_core.performance.data_types import DifficultyEnum, PerformanceStatsData
from data_types.ai_core import DifficultyScore


class LearningModeState(ABC):
    """Abstract base class for learning mode states"""

    @abstractmethod
    def get_guidance(self, difficulty_levels: int) -> str:
        """Generate guidance message based on difficulty levels"""
        pass

    @abstractmethod
    def calculate_requirements(self, difficulty_levels: int) -> tuple[int, int]:
        """Calculate required score and total questions"""
        pass

    @abstractmethod
    def get_next_state_name(self) -> str:
        """Get the name of the next state in the progression"""
        pass

    @abstractmethod
    def create_difficulty_scores(
        self,
        difficulties: List[DifficultyEnum],
        status: Literal["success", "failed"],
        stats: PerformanceStatsData,
    ) -> List[DifficultyScore]:
        """Create difficulty score objects for a list of difficulties"""
        pass

    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the name of this learning mode"""
        pass

    @property
    @abstractmethod
    def guidance_message(self) -> str:
        """Return the general guidance message for this mode"""
        pass


class BaseLearningModeState(LearningModeState):
    """Base implementation of common functionality for learning mode states"""

    def __init__(self, mode_type: LearningModeType):
        self._mode_type = mode_type
        self._rule = LearningRuleFactory.get_rule(mode_type)

    def get_guidance(self, difficulty_levels: int) -> str:
        """Generate guidance message based on difficulty levels"""
        if self._mode_type == LearningModeType.MASTERED:
            return "You've mastered all difficulty levels! Practice with unlimited questions at any time."

        required_correct = int(
            self._rule.pass_requirement
            * self._rule.questions_per_difficulty
            * difficulty_levels
        )
        total_questions = self._rule.questions_per_difficulty * difficulty_levels

        return f"To advance, correctly answer at least {required_correct} out of {total_questions} questions."

    def calculate_requirements(self, difficulty_levels: int) -> tuple[int, int]:
        """Calculate required score and total questions"""
        total_questions = self._rule.questions_per_difficulty * difficulty_levels
        required_score = int(self._rule.pass_requirement * total_questions)
        return required_score, total_questions

    def create_difficulty_scores(
        self,
        difficulties: List[DifficultyEnum],
        status: Literal["success", "failed"],
        stats: PerformanceStatsData,
    ) -> List[DifficultyScore]:
        """Create difficulty score objects for a list of difficulties"""
        fraction = Fraction(self._rule.pass_requirement).limit_denominator()
        fraction_str = f"{fraction.numerator}/{fraction.denominator}"

        return [
            DifficultyScore(
                difficulty=difficulty.value,
                status=status,
                required_score=fraction_str,
                users_score=f"{int(stats.difficulty_scores[difficulty])}/{fraction.denominator}",
            )
            for difficulty in difficulties
        ]

    @property
    def mode_name(self) -> str:
        """Return the name of this learning mode"""
        return self._mode_type.value


class NormalModeState(BaseLearningModeState):
    def __init__(self):
        super().__init__(LearningModeType.NORMAL)

    def get_next_state_name(self) -> str:
        return LearningModeType.RECOVERY.value

    @property
    def guidance_message(self) -> str:
        return "Answer the required number of questions to level up and progress through the course."


class RecoveryModeState(BaseLearningModeState):
    def __init__(self):
        super().__init__(LearningModeType.RECOVERY)

    def get_next_state_name(self) -> str:
        return LearningModeType.REINFORCEMENT.value

    @property
    def guidance_message(self) -> str:
        return "Take time to review the fundamental concepts."


class ReinforcementModeState(BaseLearningModeState):
    def __init__(self):
        super().__init__(LearningModeType.REINFORCEMENT)

    def get_next_state_name(self) -> str:
        return LearningModeType.RESET.value

    @property
    def guidance_message(self) -> str:
        return "Focus on completing questions in areas where you had difficulty."


class ResetModeState(BaseLearningModeState):
    def __init__(self):
        super().__init__(LearningModeType.RESET)

    def get_next_state_name(self) -> str:
        return LearningModeType.RESET.value

    @property
    def guidance_message(self) -> str:
        return "Start fresh with a comprehensive review."


class MasteredModeState(BaseLearningModeState):
    def __init__(self):
        super().__init__(LearningModeType.MASTERED)

    def get_next_state_name(self) -> str:
        return LearningModeType.MASTERED.value

    @property
    def guidance_message(self) -> str:
        return "Continue practicing to maintain mastery."
