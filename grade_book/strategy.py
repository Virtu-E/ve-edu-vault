from fractions import Fraction
from typing import Dict, List, Literal, Optional, Protocol

from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory
from data_types.ai_core import DifficultyScore, NextMode, PerformanceStats, PreviousMode


class LearningModeStrategy(Protocol):
    """Interface for learning mode strategies - Open/Closed Principle"""

    def get_next_mode(self) -> NextMode:
        """Determine the next learning mode"""
        pass

    def get_previous_mode(self) -> Optional[PreviousMode]:
        """Get previous mode details"""
        pass


class StandardLearningModeStrategy:
    """Concrete implementation of learning mode strategy with improved organization and error handling"""

    MODE_PROGRESSION: Dict[str, str] = {
        LearningModeType.NORMAL.value: LearningModeType.RECOVERY.value,
        LearningModeType.RECOVERY.value: LearningModeType.REINFORCEMENT.value,
        LearningModeType.REINFORCEMENT.value: LearningModeType.RESET.value,
        LearningModeType.RESET.value: LearningModeType.RESET.value,
        LearningModeType.MASTERED.value: LearningModeType.MASTERED.value,
    }

    MODE_GUIDANCE_MESSAGES: Dict[str, str] = {
        LearningModeType.NORMAL.value: "Answer the required number of questions to level up and progress through the course.",
        LearningModeType.REINFORCEMENT.value: "Focus on completing questions in areas where you had difficulty.",
        LearningModeType.RECOVERY.value: "Take time to review the fundamental concepts.",
        LearningModeType.RESET.value: "Start fresh with a comprehensive review.",
        LearningModeType.MASTERED.value: "Continue practicing to maintain mastery.",
    }

    def __init__(self, performance_stats: PerformanceStats, current_mode: str):
        self._stats = performance_stats
        self._current_mode = current_mode

    @staticmethod
    def _get_guidance(mode: LearningModeType, difficulty_levels: int) -> str:
        """Generate guidance message based on learning mode and difficulty levels"""
        if mode == LearningModeType.MASTERED:
            return "You've mastered all difficulty levels! Practice with unlimited questions at any time."

        rule = LearningRuleFactory.create_rule(mode)
        required_correct = int(
            rule.pass_requirement * rule.questions_per_difficulty * difficulty_levels
        )
        total_questions = rule.questions_per_difficulty * difficulty_levels

        return f"To advance, correctly answer at least {required_correct} out of {total_questions} questions."

    @staticmethod
    def _calculate_mode_stats(
        mode: LearningModeType, difficulty_levels: int
    ) -> tuple[int, int]:
        """Calculate required score and total questions for a given mode"""
        rule = LearningRuleFactory.create_rule(mode)
        total_questions = rule.questions_per_difficulty * difficulty_levels
        required_score = int(rule.pass_requirement * total_questions)
        return required_score, total_questions

    def _create_difficulty_scores(
        self,
        difficulties: List[Literal["easy", "medium", "hard"]],
        status: Literal["success", "failed"],
        rule,
    ) -> List[DifficultyScore]:
        """Create difficulty score objects for a list of difficulties"""

        fraction = Fraction(rule.pass_requirement).limit_denominator()
        fraction_str = f"{fraction.numerator}/{fraction.denominator}"
        return [
            DifficultyScore(
                difficulty=difficulty,
                status=status,
                required_score=fraction_str,
                users_score=f"{int(self._stats.difficulty_scores[difficulty])}/{fraction.denominator}",
            )
            for difficulty in difficulties
        ]

    def get_next_mode(self) -> NextMode:
        """Determine the next learning mode and associated guidance"""
        next_mode = self.MODE_PROGRESSION.get(self._current_mode)
        if not next_mode:
            raise ValueError(f"Invalid current mode: {self._current_mode}")

        try:
            mode_enum = LearningModeType.from_string(next_mode)
            required_score, total_questions = self._calculate_mode_stats(
                mode_enum, len(self._stats.failed_difficulties)
            )

            return NextMode(
                mode_guidance=self.MODE_GUIDANCE_MESSAGES.get(next_mode),
                guidance=self._get_guidance(
                    mode_enum, len(self._stats.failed_difficulties)
                ),
                required_score=required_score,
                total_questions=total_questions,
                mode_name=mode_enum.value,
            )
        except ValueError as e:
            raise ValueError(f"Error processing next mode: {e}")

    def get_previous_mode(self) -> Optional[PreviousMode]:
        """Get previous mode details with comprehensive statistics"""
        previous_mode = self._current_mode

        # Handle the case where there is no previous mode (i.e., normal mode)
        if previous_mode is None:
            return None

        try:
            mode_enum = LearningModeType.from_string(previous_mode)
            rule = LearningRuleFactory.create_rule(mode_enum)

            required_score, total_questions = self._calculate_mode_stats(
                mode_enum, len(self._stats.ranked_difficulties)
            )

            return PreviousMode(
                mode_guidance=self.MODE_GUIDANCE_MESSAGES.get(previous_mode),
                guidance=self._get_guidance(
                    mode_enum, len(self._stats.ranked_difficulties)
                ),
                required_score=required_score,
                total_questions=total_questions,
                failed_difficulties=self._create_difficulty_scores(
                    self._stats.failed_difficulties, "failed", rule
                ),
                passed_difficulties=self._create_difficulty_scores(
                    self._stats.passed_difficulties, "success", rule
                ),
                mode_name=mode_enum.value,
            )
        except ValueError as e:
            raise ValueError(f"Error processing previous mode: {e}")
