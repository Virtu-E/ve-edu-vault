import pytest

from ai_core.performance.calculators.base_calculator import (
    PerformanceCalculatorInterface,
)
from ai_core.performance.calculators.calculator_factory import (
    LearningModeType,
    PerformanceCalculatorFactory,
)
from ai_core.performance.calculators.normal_cal import NormalModeCalculator
from ai_core.performance.calculators.recovery_cal import RecoveryModeCalculator
from ai_core.performance.calculators.reinforcement_cal import (
    ReinforcementModeCalculator,
)


class TestPerformanceCalculatorFactory:
    """Test suite for the PerformanceCalculatorFactory class."""

    def test_create_normal_calculator(self):
        """Test creation of NormalModeCalculator."""
        calculator = PerformanceCalculatorFactory.create_calculator(
            LearningModeType.NORMAL
        )
        assert isinstance(calculator, NormalModeCalculator)
        assert isinstance(calculator, PerformanceCalculatorInterface)

    def test_create_recovery_calculator(self):
        """Test creation of RecoveryModeCalculator."""
        calculator = PerformanceCalculatorFactory.create_calculator(
            LearningModeType.RECOVERY
        )
        assert isinstance(calculator, RecoveryModeCalculator)
        assert isinstance(calculator, PerformanceCalculatorInterface)

    def test_create_reinforcement_calculator(self):
        """Test creation of ReinforcementModeCalculator."""
        calculator = PerformanceCalculatorFactory.create_calculator(
            LearningModeType.REINFORCEMENT
        )
        assert isinstance(calculator, ReinforcementModeCalculator)
        assert isinstance(calculator, PerformanceCalculatorInterface)

    @pytest.mark.parametrize(
        "mode,expected_class",
        [
            (LearningModeType.NORMAL, NormalModeCalculator),
            (LearningModeType.RECOVERY, RecoveryModeCalculator),
            (LearningModeType.REINFORCEMENT, ReinforcementModeCalculator),
        ],
    )
    def test_all_calculator_types(self, mode, expected_class):
        """Test creation of all calculator types using parametrize."""
        calculator = PerformanceCalculatorFactory.create_calculator(mode)
        assert isinstance(calculator, expected_class)
        assert isinstance(calculator, PerformanceCalculatorInterface)

    def test_calculator_uniqueness(self):
        """Test that each call creates a new instance."""
        calc1 = PerformanceCalculatorFactory.create_calculator(LearningModeType.NORMAL)
        calc2 = PerformanceCalculatorFactory.create_calculator(LearningModeType.NORMAL)
        assert calc1 is not calc2

    def test_type_validation(self):
        """Test that non-LearningModeType values raise TypeError."""
        with pytest.raises(ValueError):
            PerformanceCalculatorFactory.create_calculator("NORMAL")
