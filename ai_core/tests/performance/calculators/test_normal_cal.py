from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator
from ai_core.performance.calculators.normal_cal import NormalModeCalculator


class TestNormalModeCalculator:
    def test_initialization(self):
        """Test if calculator initializes with correct required questions"""
        calculator = NormalModeCalculator()
        assert calculator.required_correct_questions == 2

    def test_inherits_from_base_calculator(self):
        """Test if NormalModeCalculator inherits from BasePerformanceCalculator"""
        calculator = NormalModeCalculator()
        assert isinstance(calculator, BasePerformanceCalculator)
