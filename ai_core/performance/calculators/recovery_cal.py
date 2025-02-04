from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class RecoveryModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 4  # Need 4 correct questions PER difficulty
