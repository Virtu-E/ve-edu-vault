from typing import List

import pytest

from ai_core.contextual_analyzer.stats.attempts_calculator import AttemptStatsCalculator
from ai_core.tests.ai_core_factories import QuestionAIContextFactory, AttemptsFactory
from data_types.ai_core import QuestionAIContext


class TestAttemptStatsCalculator:
    @pytest.fixture
    def calculator(self):
        return AttemptStatsCalculator()

    def create_questions(self, configs: List[dict]) -> List[QuestionAIContext]:
        """Helper method to create questions based on configurations"""
        return [
            QuestionAIContextFactory(
                attempts=AttemptsFactory(
                    attemptNumber=config.get("attempt_number", 1),
                    success=config.get("success", False),
                    timeSpent=90,
                )
            )
            for config in configs
        ]

    def test_calculate_total_attempts_empty_list(self, calculator):
        """Test total attempts calculation with empty list"""
        questions = []
        assert calculator.calculate_total_attempts(questions) == 0

    def test_calculate_total_attempts(self, calculator):
        """Test total attempts calculation with various attempts"""
        questions = self.create_questions([{"attempt_number": 1}, {"attempt_number": 2}, {"attempt_number": 3}])
        assert calculator.calculate_total_attempts(questions) == 6

    def test_calculate_success_rate_empty_list(self, calculator):
        """Test success rate calculation with empty list"""
        questions = []
        assert calculator.calculate_success_rate(questions) == 0.0

    def test_calculate_success_rate_all_failed(self, calculator):
        """Test success rate calculation with all failed attempts"""
        questions = self.create_questions([{"success": False}, {"success": False}, {"success": False}])
        assert calculator.calculate_success_rate(questions) == 0.0

    def test_calculate_success_rate_all_success(self, calculator):
        """Test success rate calculation with all successful attempts"""
        questions = self.create_questions([{"success": True}, {"success": True}, {"success": True}])
        assert calculator.calculate_success_rate(questions) == 100.0

    def test_calculate_success_rate_mixed(self, calculator):
        """Test success rate calculation with mixed results"""
        questions = self.create_questions([{"success": True}, {"success": False}, {"success": True}])
        assert calculator.calculate_success_rate(questions) == 66.7

    def test_calculate_attempt_specific_rates_empty_list(self, calculator):
        """Test attempt specific rates calculation with empty list"""
        questions = []
        expected = {"first": 0.0, "second": 0.0, "third": 0.0}
        assert calculator.calculate_attempt_specific_rates(questions) == expected

    def test_calculate_attempt_specific_rates_first_attempts(self, calculator):
        """Test attempt specific rates calculation with first attempt successes"""
        questions = self.create_questions([
            {"attempt_number": 1, "success": True},
            {"attempt_number": 1, "success": True},
            {"attempt_number": 1, "success": False},
        ])
        expected = {"first": 66.7, "second": 0.0, "third": 0.0}
        assert calculator.calculate_attempt_specific_rates(questions) == expected

    def test_calculate_attempt_specific_rates_mixed_attempts(self, calculator):
        """Test attempt specific rates calculation with mixed attempt successes"""
        questions = self.create_questions([
            {"attempt_number": 1, "success": True},
            {"attempt_number": 2, "success": True},
            {"attempt_number": 3, "success": True},
            {"attempt_number": 1, "success": False},
        ])
        expected = {"first": 25.0, "second": 25.0, "third": 25.0}
        assert calculator.calculate_attempt_specific_rates(questions) == expected

    def test_max_attempts_constant(self, calculator):
        """Test that MAX_ATTEMPTS is correctly defined"""
        assert calculator.MAX_ATTEMPTS == 3

    @pytest.mark.parametrize("attempt_number", [1, 2, 3])
    def test_single_attempt_specific_rate(self, calculator, attempt_number):
        """Test specific attempt rates individually"""
        questions = self.create_questions([
            {"attempt_number": attempt_number, "success": True},
            {"attempt_number": attempt_number, "success": False},
        ])
        rates = calculator.calculate_attempt_specific_rates(questions)
        expected_rate = 50.0 if attempt_number in [1, 2, 3] else 0.0
        assert rates[{1: "first", 2: "second", 3: "third"}[attempt_number]] == expected_rate
