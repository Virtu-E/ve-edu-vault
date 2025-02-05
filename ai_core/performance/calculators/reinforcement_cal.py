from ai_core.learning_mode_rules import ReinforcementRule
from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class ReinforcementModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = ReinforcementRule.required_correct_questions
