from enum import Enum

from ai_core.performance.calculators.base_calculator import PerformanceCalculatorInterface
from ai_core.performance.calculators.normal_cal import NormalModeCalculator
from ai_core.performance.calculators.recovery_cal import RecoveryModeCalculator
from ai_core.performance.calculators.reinforcement_cal import ReinforcementModeCalculator


class CalculatorLearningMode(Enum):
    NORMAL = "normal"
    REINFORCEMENT = "reinforcement"
    RECOVERY = "recovery"


class PerformanceCalculatorFactory:
    @staticmethod
    def create_calculator(mode: CalculatorLearningMode) -> PerformanceCalculatorInterface:
        calculators = {
            CalculatorLearningMode.NORMAL: NormalModeCalculator,
            CalculatorLearningMode.RECOVERY: RecoveryModeCalculator,
            CalculatorLearningMode.REINFORCEMENT: ReinforcementModeCalculator,
        }

        calculator_class = calculators.get(mode)
        if not calculator_class:
            raise ValueError(f"Unsupported learning mode: {mode}")
        return calculator_class()
