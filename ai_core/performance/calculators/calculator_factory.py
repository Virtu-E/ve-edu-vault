from ai_core.learning_mode_rules import LearningModeType
from ai_core.performance.calculators.base_calculator import PerformanceCalculatorInterface
from ai_core.performance.calculators.normal_cal import NormalModeCalculator
from ai_core.performance.calculators.recovery_cal import RecoveryModeCalculator
from ai_core.performance.calculators.reinforcement_cal import ReinforcementModeCalculator


class PerformanceCalculatorFactory:
    @staticmethod
    def create_calculator(
        mode: LearningModeType,
    ) -> PerformanceCalculatorInterface:
        calculators = {
            LearningModeType.NORMAL: NormalModeCalculator,
            LearningModeType.RECOVERY: RecoveryModeCalculator,
            LearningModeType.REINFORCEMENT: ReinforcementModeCalculator,
        }

        calculator_class = calculators.get(mode)
        if not calculator_class:
            raise ValueError(f"Unsupported learning mode: {mode}")
        return calculator_class()
