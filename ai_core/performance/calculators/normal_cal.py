from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class NormalModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 2  # Need 2 correct questions PER difficulty
