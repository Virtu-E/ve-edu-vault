from ai_core.learning_mode_rules import LearningModeType
from ai_core.performance.data_types import PerformanceStatsData
from data_types.ai_core import NextMode, PreviousMode

from .learning_states import (
    LearningModeState,
    MasteredModeState,
    NormalModeState,
    RecoveryModeState,
    ReinforcementModeState,
    ResetModeState,
)


class LearningModeContext:
    """Context class that manages the current learning mode state"""

    def __init__(self, performance_stats: PerformanceStatsData, current_mode: str):
        self._stats = performance_stats
        self._state = self._create_state_from_name(current_mode)

    def _create_state_from_name(self, mode_name: str) -> LearningModeState:
        """Factory method to create appropriate state object"""
        if mode_name == LearningModeType.NORMAL.value:
            return NormalModeState()
        elif mode_name == LearningModeType.RECOVERY.value:
            return RecoveryModeState()
        elif mode_name == LearningModeType.REINFORCEMENT.value:
            return ReinforcementModeState()
        elif mode_name == LearningModeType.RESET.value:
            return ResetModeState()
        elif mode_name == LearningModeType.MASTERED.value:
            return MasteredModeState()
        else:
            raise ValueError(f"Invalid mode name: {mode_name}")

    def get_next_mode(self) -> NextMode:
        """Determine the next learning mode and associated guidance"""
        next_state_name = self._state.get_next_state_name()
        next_state = self._create_state_from_name(next_state_name)

        difficulty_levels = len(self._stats.failed_difficulties)
        required_score, total_questions = next_state.calculate_requirements(
            difficulty_levels
        )

        return NextMode(
            mode_guidance=next_state.guidance_message,
            guidance=next_state.get_guidance(difficulty_levels),
            required_score=required_score,
            total_questions=total_questions,
            mode_name=next_state.mode_name,
        )

    def get_previous_mode(self) -> PreviousMode:
        """Get previous mode details with comprehensive statistics"""
        # The current state is the previous mode in terms of the API
        difficulty_levels = len(self._stats.ranked_difficulties)
        required_score, total_questions = self._state.calculate_requirements(
            difficulty_levels
        )

        return PreviousMode(
            mode_guidance=self._state.guidance_message,
            guidance=self._state.get_guidance(difficulty_levels),
            required_score=required_score,
            total_questions=total_questions,
            failed_difficulties=self._state.create_difficulty_scores(
                self._stats.failed_difficulties, "failed", self._stats
            ),
            passed_difficulties=self._state.create_difficulty_scores(
                self._stats.passed_difficulties, "success", self._stats
            ),
            mode_name=self._state.mode_name,
        )

    def transition_to_state(self, mode_name: str) -> None:
        """Explicitly transition to a different state"""
        self._state = self._create_state_from_name(mode_name)
