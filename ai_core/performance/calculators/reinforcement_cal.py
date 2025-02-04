from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator


class ReinforcementModeCalculator(BasePerformanceCalculator):
    def __init__(self):
        super().__init__()
        self.required_correct_questions = 3  # 3/3 questions need to be correct / all questions on the difficulty cleared
