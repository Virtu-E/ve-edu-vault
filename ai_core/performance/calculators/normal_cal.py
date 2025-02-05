from ai_core.learning_mode_rules import NormalRule
from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class NormalModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = NormalRule.required_correct_questions
