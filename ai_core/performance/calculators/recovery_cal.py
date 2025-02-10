from ai_core.learning_mode_rules import RecoveryRule
from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class RecoveryModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = RecoveryRule.required_correct_questions
