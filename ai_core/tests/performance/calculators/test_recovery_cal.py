from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator
from ai_core.performance.calculators.recovery_cal import RecoveryModeCalculator


class TestRecoveryModeCalculator:
    def test_initialization(self):
        """Test if calculator initializes with correct required questions"""
        calculator = RecoveryModeCalculator()
        assert calculator.required_correct_questions == 4

    def test_inherits_from_base_calculator(self):
        """Test if RecoveryModeCalculator inherits from BasePerformanceCalculator"""
        calculator = RecoveryModeCalculator()
        assert isinstance(calculator, BasePerformanceCalculator)
