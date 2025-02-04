from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator
from ai_core.performance.calculators.reinforcement_cal import (
    ReinforcementModeCalculator,
)


class TestReinforcementModeCalculator:
    def test_initialization(self):
        """Test if calculator initializes with correct required questions"""
        calculator = ReinforcementModeCalculator()
        assert calculator.required_correct_questions == 3

    def test_inherits_from_base_calculator(self):
        """Test if ReinforcementModeCalculator inherits from BasePerformanceCalculator"""
        calculator = ReinforcementModeCalculator()
        assert isinstance(calculator, BasePerformanceCalculator)
